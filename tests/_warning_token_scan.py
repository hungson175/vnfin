"""Forward-discovery extractor for ``result.warnings`` tokens (issue #188).

The #180 lockstep guard (``test_skill_warning_tokens_section_in_lockstep_with_code``)
iterates only over the hardcoded ``_WARNING_TOKENS_180`` tuple, so a token a dev EMITS in
``vnfin/`` but never adds to the tuple is invisible to it — exactly how 4 undocumented
warnings shipped historically. This module DISCOVERS the emitted token set straight from the
code AST so the guard can assert ``code-emits ⊆ documented`` and a new emission with no doc
row goes red automatically.

It is TEST-INFRASTRUCTURE ONLY (no ``vnfin/`` import or change). The extractor is pure (it
takes source TEXT), so unit tests can feed it synthetic snippets per emission shape.

Def-use trace closes the old blind spot (issue #192 landed)
-----------------------------------------------------------
The forward scan keys on emission positions named ``warnings`` / ``*_warnings`` (plus
``_*warning(s)`` helper returns). Tokens accumulated into an intermediate list named something
ELSE — ``warns`` / ``note`` / ``dup_notes`` — before being spread into a ``warnings=`` arg used
to be invisible. That historically affected five DOCUMENTED tokens: ``partial_start_coverage``,
``partial_end_coverage``, ``skipped_period_rows``, ``skipped_mismatched_report_rows``,
``cross_board_duplicate_symbol``.

#192 closes it with a SMALL intra-function def-use trace (NOT a generic var-name broadening,
which would false-positive-red on incidental ``note``/``warns`` vars — the reason #188 kept the
precise name regex). Within each ``FunctionDef`` scope we (1) collect the normalized token
candidates assigned/``.append``/``.extend``-ed to every local; (2) identify the locals that
demonstrably FLOW INTO a warnings sink — inside a ``warnings=`` kwarg value (directly, wrapped
``tuple(VAR)``, or as a ``BinOp`` operand of it), or as the arg of ``.extend``/a ``+``/``+=``
concatenation INTO a ``(^|_)warnings$`` accumulator, or (for a ``_*warning(s)`` helper) inside
its RETURN value; (3) add only those sink-flowing locals' literals. The trace is intra-function
(no cross-function flow needed for these five). The REVERSE #180 lockstep test still
independently pins every documented token as a code literal.
"""
from __future__ import annotations

import ast
import pathlib
import re

# Targets whose value flows into a ``result.warnings`` tuple.
#   - a Name target ``warnings`` / ``*_warnings`` (Assign / AugAssign / AnnAssign)
#   - the receiver of a ``.append`` / ``.extend`` call
_WARNINGS_TARGET_RE = re.compile(r"(^|_)warnings$")
# A ``_*warnings`` helper (Shape D). Also matches the singular ``_*warning`` helpers
# (``_phantom_tail_warning``, ``_nav_end_gap_warning``, ``_series_end_gap_warning``,
# ``_partial_warning``) whose RETURN directly carries the token f-string/literal — they are
# part of the documented emission corpus too. Deliberately does NOT match ``*reason`` helpers
# (e.g. ``_warnings_reason``), which return diagnostic strings, not ``.warnings`` tokens.
_WARNINGS_HELPER_RE = re.compile(r"_.*warnings?$")


# Allowlist seam (NOT YAGNI): any future deliberate non-token literal that lands in a
# ``warnings=`` position is subtracted here, WITH a ``# reason:`` comment — never by weakening
# the matcher. Initially empty: the matcher is precise enough that nothing needs excusing.
_NON_TOKEN_WARNING_LITERALS: frozenset[str] = frozenset()


def _normalize(candidate: str) -> str:
    """A raw candidate string → its warning TOKEN: the segment before the first ``:``.

    A trailing ``_`` is KEPT (the ``*_leg_`` declared-family prefixes). Whitespace stripped.
    """
    return candidate.split(":", 1)[0].strip()


class _WarningTokenVisitor(ast.NodeVisitor):
    """Walk a module AST; collect candidate warning-token strings from every emission
    position, resolving module/class/function-level single-str-Constant names."""

    def __init__(self) -> None:
        # Flat name→literal map (module/class/function scope). Collisions are vanishingly
        # rare in this codebase; last-write-wins is acceptable per the spec.
        self.name_to_literal: dict[str, str] = {}
        self.candidates: set[str] = set()

    # --- pass 1: build the name→literal map -------------------------------------------- #
    def _record_const_name(self, target: ast.expr, value: ast.expr) -> None:
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            self.name_to_literal[target.id] = value.value

    # --- emission-position detection --------------------------------------------------- #
    @staticmethod
    def _is_warnings_name(node: ast.expr) -> bool:
        return isinstance(node, ast.Name) and bool(_WARNINGS_TARGET_RE.search(node.id))

    def visit_Assign(self, node: ast.Assign) -> None:
        # name→literal map (single-target single-str-Constant)
        if len(node.targets) == 1:
            self._record_const_name(node.targets[0], node.value)
        # emission: any target Name matching ``(^|_)warnings$``
        if any(self._is_warnings_name(t) for t in node.targets):
            self._collect_from_value(node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self._record_const_name(node.target, node.value)
            if self._is_warnings_name(node.target):
                self._collect_from_value(node.value)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        # e.g. ``warnings += (token,)``
        if self._is_warnings_name(node.target):
            self._collect_from_value(node.value)
        self.generic_visit(node)

    def visit_keyword(self, node: ast.keyword) -> None:
        # any ``warnings=<value>`` keyword arg in any Call
        if node.arg == "warnings":
            self._collect_from_value(node.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # ``<warnings-ish>.append(...)`` / ``.extend(...)``
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr in ("append", "extend")
            and self._is_warnings_name(func.value)
        ):
            for arg in node.args:
                self._collect_from_value(arg)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # a ``_*warnings`` (or ``_*warning``) helper → scan every RETURN value (Shape D)
        if _WARNINGS_HELPER_RE.search(node.name):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and sub.value is not None:
                    self._collect_from_value(sub.value)
        # #192 def-use trace: locals that flow INTO a warnings sink within this function.
        self._trace_local_warnings_flow(node)
        self.generic_visit(node)

    # --- #192 intra-function def-use trace --------------------------------------------- #
    def _trace_local_warnings_flow(self, node: ast.FunctionDef) -> None:
        """Find locals whose accumulated literals FLOW INTO a warnings sink in this function,
        and add those literals. Catches ``dup_notes``/``warns``/``note``-style accumulators
        WITHOUT matching the variable NAME — only by demonstrated dataflow into a sink.
        """
        is_helper = bool(_WARNINGS_HELPER_RE.search(node.name))

        # 1) local_literals: every local var -> normalized candidates assigned/appended/extended.
        local_literals: dict[str, set[str]] = {}

        def _bucket(name: str) -> set[str]:
            return local_literals.setdefault(name, set())

        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    if isinstance(tgt, ast.Name):
                        self._collect_into(sub.value, _bucket(tgt.id))
            elif isinstance(sub, ast.AnnAssign) and sub.value is not None:
                if isinstance(sub.target, ast.Name):
                    self._collect_into(sub.value, _bucket(sub.target.id))
            elif isinstance(sub, ast.AugAssign):
                if isinstance(sub.target, ast.Name):
                    self._collect_into(sub.value, _bucket(sub.target.id))
            elif isinstance(sub, ast.Call):
                func = sub.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr in ("append", "extend")
                    and isinstance(func.value, ast.Name)
                ):
                    for arg in sub.args:
                        self._collect_into(arg, _bucket(func.value.id))

        if not local_literals:
            return

        # 2) sink-flowing locals: a local Name reaching a warnings sink position.
        sink_locals: set[str] = set()

        def _operand_names(value: ast.expr) -> set[str]:
            """Names that reach a warnings VALUE position: directly, wrapped ``tuple(VAR)``,
            or as a (recursive) BinOp operand of it."""
            names: set[str] = set()

            def _walk(v: ast.expr) -> None:
                if isinstance(v, ast.Name):
                    names.add(v.id)
                elif isinstance(v, ast.BinOp):
                    _walk(v.left)
                    _walk(v.right)
                elif isinstance(v, (ast.Tuple, ast.List, ast.Set)):
                    for elt in v.elts:
                        _walk(elt)
                elif isinstance(v, ast.Call):
                    # unwrap ``tuple(VAR)`` / ``list(VAR)`` etc.
                    for a in v.args:
                        _walk(a)

            _walk(value)
            return names

        for sub in ast.walk(node):
            # (a) inside a ``warnings=`` kwarg value
            if isinstance(sub, ast.keyword) and sub.arg == "warnings":
                sink_locals |= _operand_names(sub.value)
            # (b) ``+=``/``=`` (BinOp) INTO a ``(^|_)warnings$`` accumulator
            elif isinstance(sub, ast.AugAssign) and self._is_warnings_name(sub.target):
                sink_locals |= _operand_names(sub.value)
            elif (
                isinstance(sub, ast.Assign)
                and any(self._is_warnings_name(t) for t in sub.targets)
                and isinstance(sub.value, ast.BinOp)
            ):
                sink_locals |= _operand_names(sub.value)
            # (b) ``<warnings-ish>.extend(VAR)``
            elif isinstance(sub, ast.Call):
                func = sub.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "extend"
                    and self._is_warnings_name(func.value)
                ):
                    for arg in sub.args:
                        sink_locals |= _operand_names(arg)
            # (c) for a ``_*warning(s)`` helper, its RETURN value is a warnings sink
            elif is_helper and isinstance(sub, ast.Return) and sub.value is not None:
                sink_locals |= _operand_names(sub.value)

        # 3) add each sink-flowing local's accumulated literals.
        for name in sink_locals:
            self.candidates |= local_literals.get(name, set())

    # --- candidate extraction from a value expression ---------------------------------- #
    def _collect_from_value(self, node: ast.expr) -> None:
        """Walk an emission value expression and add any token candidate to ``self.candidates``."""
        self._collect_into(node, self.candidates)

    def _collect_into(self, node: ast.expr, sink: set[str]) -> None:
        """Walk a value expression and add any token candidate found into ``sink``.

        Recurses through Tuple/List/Set/BinOp/IfExp containers so
        ``("tok",) + tuple(other)`` and ``("tok",) if cond else ()`` both yield ``tok``.
        Leaf forms: Constant str, Name (resolved via the map), JoinedStr (static prefix).
        Pure pass-throughs (``tuple(hist.warnings)``, ``other.warnings``) yield nothing.
        """
        if node is None:
            return
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                tok = _normalize(node.value)
                if tok:
                    sink.add(tok)
            return
        if isinstance(node, ast.Name):
            literal = self.name_to_literal.get(node.id)
            if literal is not None:
                tok = _normalize(literal)
                if tok:
                    sink.add(tok)
            return
        if isinstance(node, ast.JoinedStr):
            prefix = self._static_prefix(node)
            if prefix is not None:
                tok = _normalize(prefix)
                if tok:
                    sink.add(tok)
            return
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for elt in node.elts:
                self._collect_into(elt, sink)
            return
        if isinstance(node, ast.BinOp):
            self._collect_into(node.left, sink)
            self._collect_into(node.right, sink)
            return
        if isinstance(node, ast.IfExp):
            self._collect_into(node.body, sink)
            self._collect_into(node.orelse, sink)
            return
        # Calls (e.g. ``tuple(...)``), comprehensions, attributes → nothing to extract.

    def _static_prefix(self, node: ast.JoinedStr) -> str | None:
        """Build the leading STATIC prefix of an f-string: concatenate, in order, each
        ``Constant`` str and each ``FormattedValue`` whose ``.value`` is a Name that RESOLVES
        to a str literal; STOP at the first unresolved ``FormattedValue`` (a dynamic
        ``{detail}``/``{len(...)}``/``{w}``). Returns ``None`` when no static lead exists.
        """
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
                continue
            if isinstance(value, ast.FormattedValue):
                inner = value.value
                if isinstance(inner, ast.Name):
                    resolved = self.name_to_literal.get(inner.id)
                    if resolved is not None:
                        parts.append(resolved)
                        continue
                # unresolved dynamic field → static prefix ends here
                break
            # any other node type ends the static prefix
            break
        if not parts:
            return None
        return "".join(parts)


def _extract_warning_tokens_from_source(src_text: str) -> set[str]:
    """Pure extractor: parse ``src_text`` and return the set of warning TOKENS its
    ``result.warnings`` emission positions can produce."""
    tree = ast.parse(src_text)
    visitor = _WarningTokenVisitor()
    visitor.visit(tree)
    return set(visitor.candidates)


def _discover_emitted_warning_tokens(repo_root) -> dict[str, list[str]]:
    """Walk ``vnfin/**/*.py`` and return ``{token: [locations]}`` for every emitted warning
    token. ``locations`` is a list of source-file paths (relative to ``repo_root``) — enough
    to point at the offending file in a failure message."""
    root = pathlib.Path(repo_root)
    vnfin_dir = root / "vnfin"
    discovered: dict[str, list[str]] = {}
    for path in sorted(vnfin_dir.rglob("*.py")):
        try:
            src = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tokens = _extract_warning_tokens_from_source(src)
        except SyntaxError:
            continue
        if not tokens:
            continue
        rel = str(path.relative_to(root))
        for tok in tokens:
            discovered.setdefault(tok, []).append(rel)
    return discovered


def _covered(e: str, documented: tuple[str, ...]) -> bool:
    """A discovered normalized token ``e`` is "documented" iff some ``t`` in ``documented``
    matches it. REVIEWER REFINEMENT: prefix-match ONLY when ``t`` ends with ``_`` (a declared
    FAMILY prefix, e.g. ``world_reference_gold_leg_``); otherwise require an EXACT match.

    A blanket ``startswith`` would let a documented SHORT token silently cover an undocumented
    LONGER emission — the exact false-negative #188 closes. So ``partial_coverage`` does NOT
    cover ``partial_coverage_xyz``; only the ``_``-suffixed leg families prefix-cover.
    """
    for t in documented:
        if t.endswith("_"):
            if e.startswith(t):
                return True
        else:
            if e == t:
                return True
    return False
