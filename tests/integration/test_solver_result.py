"""Malformed, mismatched and JSON-encoded solver output at the GUI boundary."""

import copy
import json
import unittest

from src.gui.solver.result import ACTIONS, make_result, validate_result
from .test_solver_gui_backend import load, start_of


def solved_result(game_map, state, algorithm="BFS", actions=None):
    actions = ["RIGHT", "RIGHT"] if actions is None else actions
    result = make_result(game_map, state, algorithm, 60.0, "SOLVED")
    result["actions"] = list(actions)
    result["metrics"].update(solution_length=len(actions), solution_cost=len(actions))
    return result


class ResultTest(unittest.TestCase):
    def setUp(self):
        self.game_map = load("basic_01.json")
        self.state = start_of(self.game_map)
        self.result = solved_result(self.game_map, self.state)

    def validate(self, result):
        return validate_result(result, self.game_map, self.state, "BFS", 60.0)

    def test_json_and_dict_are_accepted_and_owned(self):
        self.assertEqual(self.validate(json.dumps(self.result)), self.result)
        validated = self.validate(self.result)
        self.result["actions"].clear()
        self.assertEqual(validated["actions"], ["RIGHT", "RIGHT"])

    def test_invalid_envelopes(self):
        for raw in (None, [], 42, "broken JSON", "null", {"status": "SOLVED"}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.validate(raw)

    def test_identity_and_contract_mismatches(self):
        for field, value in (("schema_version", True), ("schema_version", 2),
                             ("map_id", "other"), ("algorithm", "DFS"),
                             ("status", []), ("status", "UNKNOWN"),
                             ("timeout_s", 1), ("cost_model", "other"),
                             ("heuristic", "other"), ("error", "unexpected")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.validate({**self.result, field: value})

    def test_snapshot_mismatch_and_bad_coordinate_types(self):
        for field, value in (("cells", [[1, 2]]), ("cells", [[True, 1]]),
                             ("cells", []), ("active", False),
                             ("bridges", {"b01": 1}), ("mode", "SPLIT")):
            result = copy.deepcopy(self.result)
            result["start_state"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.validate(result)

    def test_bridge_tuple_uses_sorted_ids_and_is_checked(self):
        game_map = {**self.game_map, "bridges": [{"id": "b02"}, {"id": "b01"}]}
        state = {**self.state, "bridges": (True, False)}
        result = solved_result(game_map, state)
        self.assertEqual(result["start_state"]["bridges"], {"b01": True, "b02": False})
        validate_result(result, game_map, state, "BFS", 60.0)
        result["start_state"]["bridges"]["b01"] = False
        with self.assertRaisesRegex(ValueError, "snapshot"):
            validate_result(result, game_map, state, "BFS", 60.0)

    def test_invalid_measurements(self):
        cases = [(name, value) for name in ("search_time_s", "peak_memory_bytes", "expanded_nodes")
                 for value in (-1, True, "12", float("nan"), float("inf"), 10**400)]
        cases += [("peak_memory_bytes", 1.5), ("expanded_nodes", 1.5),
                  ("solution_length", 1), ("solution_length", True),
                  ("solution_cost", 1), ("solution_cost", 2.5)]
        for field, value in cases:
            result = copy.deepcopy(self.result)
            result["metrics"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.validate(result)
        for metrics in (None, [], {}):
            with self.subTest(metrics=metrics), self.assertRaises(ValueError):
                self.validate({**self.result, "metrics": metrics})

    def test_invalid_actions_and_missing_metrics(self):
        for actions in (None, "RIGHT", ["TELEPORT"], [42], [["RIGHT"]]):
            with self.subTest(actions=actions), self.assertRaises(ValueError):
                self.validate({**self.result, "actions": actions})
        for key in self.result["metrics"]:
            result = copy.deepcopy(self.result)
            del result["metrics"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(result)

    def test_switch_can_be_valid_but_unsupported_by_current_game(self):
        result = solved_result(self.game_map, self.state, actions=["SWITCH"])
        self.validate(result)
        with self.assertRaisesRegex(ValueError, "does not support SWITCH"):
            validate_result(result, self.game_map, self.state, "BFS", 60.0,
                            supported_actions=ACTIONS - {"SWITCH"})

    def test_non_solved_results_require_null_solution(self):
        for status in ("TIMEOUT", "CANCELLED", "UNSOLVABLE", "ERROR"):
            result = make_result(self.game_map, self.state, "BFS", 60.0, status,
                                 "failed" if status == "ERROR" else None)
            self.validate(result)
            result["actions"] = []
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.validate(result)

    def test_empty_solution_requires_zero_cost_and_expanded(self):
        result = solved_result(self.game_map, self.state, actions=[])
        self.validate(result)
        result["metrics"]["expanded_nodes"] = 1
        with self.assertRaises(ValueError):
            self.validate(result)

    def test_astar_heuristic_and_error_message(self):
        result = solved_result(self.game_map, self.state, algorithm="ASTAR")
        validate_result(result, self.game_map, self.state, "ASTAR", 60.0)
        for error in (None, "", [], 42):
            result = make_result(self.game_map, self.state, "BFS", 60.0, "ERROR", error)
            with self.subTest(error=error), self.assertRaises(ValueError):
                self.validate(result)

    def test_error_result_allows_null_unvalidated_envelope_fields(self):
        for field in ("map_id", "start_state", "timeout_s"):
            with self.subTest(field=field):
                result = make_result(self.game_map, self.state, "BFS", 60.0, "ERROR", "bad input")
                result[field] = None
                self.assertEqual(self.validate(result)[field], None)
                non_error = make_result(self.game_map, self.state, "BFS", 60.0, "TIMEOUT")
                non_error[field] = None
                with self.assertRaises(ValueError):
                    self.validate(non_error)

