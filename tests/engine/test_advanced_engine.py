"""Contract-level tests of advanced mechanics using real map JSON and states."""
import copy
import dataclasses
import unittest

from src.engine import (Action, Mode, State, Status, initial_state, is_goal, parse_map,
                        state_from_dict, state_key, state_to_dict, step_cost,
                        successors, transition, validate_state)
from src.solvers.costs.calc import calculate_step_cost


def fixture(tiles=(), bridges=(), switches=()):
    grid = [["floor"] * 8 for _ in range(8)]
    grid[7][7] = "goal"
    for row, col, tile in tiles:
        grid[row][col] = tile
    return {"schema_version": 1, "id": "advanced", "name": "Advanced fixture",
            "difficulty": "medium", "rows": 8, "cols": 8, "grid": grid,
            "start": [0, 0], "bridges": list(bridges), "switches": list(switches),
            "source": {"kind": "original", "reference": "Engine contract tests"}}


def bridge(ident="b01", cell=(3, 4), opened=False):
    return {"id": ident, "cells": [list(cell)], "initial_open": opened}


def switch(typ="soft", cell=(3, 3), ident="s01", mode="toggle", targets=("b01",), opened=True):
    effect = {"mode": mode, "targets": list(targets)}
    if mode == "permanent":
        effect["open"] = opened
    return {"id": ident, "cell": list(cell), "type": typ, "effect": effect}


def split_switch(dest=((5, 5), (1, 1)), active=0):
    return {"id": "split01", "cell": [3, 3], "type": "split",
            "destinations": [list(c) for c in dest], "active_destination": active}


class AdvancedRulesTest(unittest.TestCase):
    def switch_map(self, typ="soft", opened=False, mode="toggle"):
        return parse_map(fixture([(3, 3, typ), (3, 4, "bridge")],
                                 [bridge(opened=opened)], [switch(typ=typ, mode=mode)]))

    def test_bridge_closed_loses_and_open_supports(self):
        m = self.switch_map()
        before = State("HORIZONTAL", ((3, 2), (3, 3)), bridges=(False,))
        self.assertEqual(transition(m, before, "RIGHT").reason, "CLOSED_BRIDGE")
        before = dataclasses.replace(before, bridges=(True,))
        self.assertEqual(transition(m, before, "RIGHT").status, Status.OK)

    def test_soft_activation_updates_bridge_and_cost(self):
        m = self.switch_map()
        before = State("UPRIGHT", ((3, 1),), bridges=(False,))
        result = transition(m, before, "RIGHT")
        self.assertEqual(result.next_state.bridges, (True,))
        self.assertEqual([e["type"] for e in result.events], ["SWITCH_ACTIVATED", "BRIDGE_CHANGED"])
        self.assertEqual(step_cost(m, before, "RIGHT", result.next_state), 2)
        self.assertEqual(calculate_step_cost(m, before, result.next_state, "RIGHT"), 2)
        self.assertEqual(transition(m, result.next_state, "RIGHT").status, Status.OK)

    def test_heavy_lying_does_not_trigger_and_standing_does(self):
        m = self.switch_map("heavy")
        before = State("UPRIGHT", ((3, 1),), bridges=(False,))
        lying = transition(m, before, "RIGHT")
        self.assertFalse(lying.next_state.bridges[0])
        self.assertEqual(lying.events, ())
        before = State("HORIZONTAL", ((3, 1), (3, 2)), bridges=(False,))
        standing = transition(m, before, "RIGHT")
        self.assertTrue(standing.next_state.bridges[0])
        self.assertEqual(step_cost(m, before, "RIGHT", standing.next_state), 2)

    def test_permanent_repeat_has_activation_but_no_redundant_bridge_event(self):
        m = self.switch_map(mode="permanent")
        before = State("HORIZONTAL", ((3, 1), (3, 2)), bridges=(True,))
        result = transition(m, before, "RIGHT")
        self.assertEqual(result.next_state.bridges, (True,))
        self.assertEqual([e["type"] for e in result.events], ["SWITCH_ACTIVATED"])
        self.assertEqual(step_cost(m, before, "RIGHT", result.next_state), 2)

    def test_single_cube_soft_and_held_switch_does_not_retrigger(self):
        m = self.switch_map()
        before = State("SPLIT", ((1, 1), (3, 2)), active=1, bridges=(False,))
        result = transition(m, before, "RIGHT")
        self.assertTrue(result.next_state.bridges[0])
        selected = transition(m, result.next_state, "SWITCH")
        held = transition(m, selected.next_state, "UP")
        self.assertTrue(held.next_state.bridges[0])
        self.assertEqual(held.events, ())
        self.assertEqual(step_cost(m, selected.next_state, "UP", held.next_state), 1)

    def test_single_cube_cannot_trigger_heavy_or_goal(self):
        m = self.switch_map("heavy")
        before = State("SPLIT", ((1, 1), (3, 2)), active=1, bridges=(False,))
        result = transition(m, before, "RIGHT")
        self.assertFalse(result.next_state.bridges[0])
        goal = State("SPLIT", ((1, 1), (7, 7)), active=1, bridges=(False,))
        self.assertFalse(is_goal(m, goal))

    def test_switch_closing_support_under_other_cube_loses_with_events(self):
        m = parse_map(fixture([(2, 2, "bridge"), (2, 3, "soft")],
                              [bridge(cell=(2, 2), opened=True)], [switch(cell=(2, 3))]))
        before = State("SPLIT", ((2, 2), (3, 3)), active=1, bridges=(True,))
        result = transition(m, before, "UP")
        self.assertEqual((result.status, result.reason), (Status.LOST, "CLOSED_BRIDGE"))
        self.assertIsNone(result.next_state)
        self.assertEqual(result.events[-1]["type"], "BRIDGE_CHANGED")
        self.assertNotIn("UP", [s.action for s in successors(m, before)])

    def test_simultaneous_effects_follow_sorted_ids(self):
        data = fixture([(3, 2, "soft"), (3, 3, "soft"), (6, 6, "bridge")],
                       [bridge(cell=(6, 6))],
                       [switch(cell=(3, 3), ident="s02"), switch(cell=(3, 2), mode="permanent")])
        m = parse_map(data)
        before = State("UPRIGHT", ((3, 1),), bridges=(False,))
        result = transition(m, before, "RIGHT")
        self.assertEqual(result.next_state.bridges, (False,))
        self.assertEqual([e["switch_id"] for e in result.events if e["type"] == "SWITCH_ACTIVATED"], ["s01", "s02"])
        self.assertEqual(step_cost(m, before, "RIGHT", result.next_state), 3)

    def test_split_preserves_destination_selection_and_switch_cost(self):
        m = parse_map(fixture([(3, 3, "split")], switches=[split_switch()]))
        before = State("HORIZONTAL", ((3, 1), (3, 2)))
        result = transition(m, before, "RIGHT")
        self.assertEqual(result.next_state.cells, ((1, 1), (5, 5)))
        self.assertEqual(result.next_state.active, 1)
        self.assertEqual(step_cost(m, before, "RIGHT", result.next_state), 1)
        changed = transition(m, result.next_state, "SWITCH")
        self.assertEqual(changed.next_state.active, 0)
        self.assertEqual(changed.events, ())
        self.assertEqual(step_cost(m, result.next_state, "SWITCH", changed.next_state), 1)

    def test_merge_in_each_axis_and_no_diagonal_merge(self):
        m = parse_map(fixture())
        for cells, action, mode in [(((2, 2), (2, 4)), "RIGHT", Mode.HORIZONTAL),
                                    (((2, 2), (4, 2)), "DOWN", Mode.VERTICAL),
                                    (((2, 2), (3, 4)), "RIGHT", Mode.SPLIT)]:
            with self.subTest(mode=mode):
                result = transition(m, State("SPLIT", cells, 0), action)
                self.assertEqual(result.next_state.mode, mode)
                if mode != Mode.SPLIT:
                    self.assertIsNone(result.next_state.active)
                    self.assertEqual(result.events[-1]["type"], "BLOCK_MERGED")

    def test_active_survives_input_sort_and_movement_resort(self):
        m = parse_map(fixture())
        before = State("SPLIT", ((3, 2), (2, 5)), 0)
        self.assertEqual(before.active, 1)
        after = transition(m, before, "UP").next_state
        self.assertEqual(after.cells[after.active], (2, 2))

    def test_split_merge_does_not_chain_trigger_heavy(self):
        m = self.switch_map("heavy")
        before = State("SPLIT", ((3, 1), (3, 3)), 0, (False,))
        result = transition(m, before, "RIGHT")
        self.assertEqual(result.next_state.mode, Mode.HORIZONTAL)
        self.assertFalse(result.next_state.bridges[0])

    def test_cubes_are_safe_on_fragile(self):
        m = parse_map(fixture([(3, 3, "fragile")]))
        before = State("SPLIT", ((1, 1), (3, 2)), 1)
        result = transition(m, before, "RIGHT")
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(step_cost(m, before, "RIGHT", result.next_state), 3)

    def test_key_and_json_include_bridges_and_active(self):
        m = self.switch_map()
        a = State("SPLIT", ((1, 1), (2, 5)), 0, (False,))
        b = dataclasses.replace(a, bridges=(True,))
        c = dataclasses.replace(a, active=1)
        self.assertEqual(len({state_key(a), state_key(b), state_key(c)}), 3)
        self.assertEqual(state_from_dict(m, state_to_dict(m, a)), a)
        with self.assertRaisesRegex(ValueError, "bridge flags"):
            validate_state(m, State("UPRIGHT", ((1, 1),)))

    def test_input_data_and_states_are_not_mutated(self):
        data = fixture([(3, 3, "soft"), (3, 4, "bridge")], [bridge()], [switch()])
        saved = copy.deepcopy(data)
        m = parse_map(data)
        state = State("UPRIGHT", ((3, 1),), bridges=(False,))
        key = state_key(state)
        transition(m, state, "RIGHT")
        self.assertEqual(data, saved)
        self.assertEqual(state_key(state), key)


class AdvancedValidationTest(unittest.TestCase):
    def setUp(self):
        self.data = fixture([(3, 3, "soft"), (3, 4, "bridge")], [bridge()], [switch()])

    def reject(self, mutate, message):
        data = copy.deepcopy(self.data)
        mutate(data)
        with self.assertRaisesRegex(ValueError, message):
            parse_map(data)

    def test_bridge_coverage_duplicates_and_wrong_tiles(self):
        self.reject(lambda d: d.update(bridges=[]), "every bridge tile")
        self.reject(lambda d: d["bridges"].append(copy.deepcopy(d["bridges"][0])), "duplicate bridge ID")
        self.reject(lambda d: d["bridges"][0]["cells"].append([3, 4]), "assigned more than once")
        self.reject(lambda d: d["bridges"][0].update(cells=[[1, 1]]), "not a bridge")
        self.reject(lambda d: d["bridges"][0].update(initial_open=1), "expected bool")

    def test_switch_targets_and_metadata(self):
        self.reject(lambda d: d["switches"][0]["effect"].update(targets=["missing"]), "unknown bridge")
        self.reject(lambda d: d["switches"][0]["effect"].update(targets=["b01", "b01"]), "duplicate bridge")
        self.reject(lambda d: d["switches"][0]["effect"].update(open=True), "unknown field")
        self.reject(lambda d: d.update(switches=[]), "every switch tile")
        self.reject(lambda d: d["switches"][0].update(cell=[3, 4]), "does not match")

    def test_permanent_requires_bool_and_unknown_fields_are_rejected(self):
        self.reject(lambda d: d["switches"][0]["effect"].update(mode="permanent"), "missing field")
        self.reject(lambda d: d["switches"][0]["effect"].update(mode="permanent", open=1), "expected bool")
        self.reject(lambda d: d["bridges"][0].update(extra=1), "unknown field")
        self.reject(lambda d: d.update(expected_solvable=None), "expected_solvable")

    def test_split_destinations_and_active_are_validated(self):
        data = fixture([(3, 3, "split")], switches=[split_switch()])
        for dest, active in [([[1,1],[1,1]],0), ([[1,1],[1,2]],0), ([[1,1],[3,3]],0), ([[1,1],[5,5]],True)]:
            with self.subTest(dest=dest, active=active):
                d=copy.deepcopy(data); d["switches"][0].update(destinations=dest, active_destination=active)
                with self.assertRaises(ValueError): parse_map(d)

    def test_bridge_ids_are_sorted_independently_of_json_order(self):
        m = parse_map(fixture([(1,1,"bridge"),(1,2,"bridge")],
                              [bridge("b02", (1,2), True), bridge("b01", (1,1), False)]))
        self.assertEqual(m.bridge_ids, ("b01", "b02"))
        self.assertEqual(initial_state(m).bridges, (False, True))


if __name__ == "__main__":
    unittest.main()
