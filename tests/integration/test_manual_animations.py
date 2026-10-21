"""Visual state regressions: falling completion and engine-driven bridge motion."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
from pathlib import Path
from unittest.mock import patch
import pygame
from src.engine import initial_state, load_map, parse_map, State
from src.gui.manual import game
from src.gui.manual.animations import BridgeAnimator, BRIDGE_DURATION

ROOT = Path(__file__).resolve().parents[2]


class ManualAnimationTest(unittest.TestCase):
    def test_bridge_events_animate_both_directions_and_reset(self):
        m = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        visual = BridgeAnimator()
        visual.reset(m, initial_state(m))
        event = {"type":"BRIDGE_CHANGED", "bridge_id":"b01", "before":False, "after":True}
        visual.trigger([event])
        self.assertTrue(visual.busy)
        visual.update(BRIDGE_DURATION/2)
        self.assertAlmostEqual(visual.tile_levels(m)[(1,4)], 0.5)
        visual.update(BRIDGE_DURATION)
        self.assertEqual(visual.tile_levels(m)[(1,4)], 1)
        self.assertFalse(visual.busy)
        visual.trigger([dict(event, before=True, after=False)])
        visual.update(BRIDGE_DURATION/2)
        self.assertAlmostEqual(visual.tile_levels(m)[(1,4)], 0.5)
        visual.reset(m, initial_state(m))
        self.assertEqual(visual.tile_levels(m)[(1,4)], 0)
        self.assertFalse(visual.busy)

    def test_opposing_events_use_final_bridge_state(self):
        m = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        visual = BridgeAnimator(); visual.reset(m, initial_state(m))
        visual.trigger([{"type":"BRIDGE_CHANGED","bridge_id":"b01","before":False,"after":True},
                        {"type":"BRIDGE_CHANGED","bridge_id":"b01","before":True,"after":False}])
        self.assertFalse(visual.busy)
        self.assertEqual(visual.values["b01"], 0)

    def test_void_falls_finish_before_game_over_message(self):
        for upright in (False, True):
            with self.subTest(upright=upright):
                grid = [["void"]*6 for _ in range(3)]
                grid[0][0] = "goal"
                for col in ((1,2,3) if upright else (1,2)):
                    grid[1][col] = "floor"
                m = parse_map({"schema_version":1,"id":"fall","name":"fall", "difficulty":"easy",
                               "rows":3,"cols":6,"grid":grid,"start":[1,1],"bridges":[],"switches":[],
                               "source":{"kind":"original","reference":"animation regression"}})
                frame=0; falls=[]; messages=[]
                original_text=game._text
                def text(*args, **kwargs):
                    if str(args[2]).startswith("Game over!"):
                        messages.append(frame)
                    return original_text(*args, **kwargs)
                def events():
                    nonlocal frame
                    frame += 1
                    if frame == 1:
                        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,
                                                  pos=(game.WIDTH//2,game.HEIGHT//2-10))]
                    if frame == 2:
                        return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)]
                    if frame == 3 or (upright and frame == 10):
                        return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT)]
                    if frame >= 30:
                        return [pygame.event.Event(pygame.QUIT)]
                    return []
                def falling(screen, state, camera, progress, action, supported):
                    falls.append((frame,state,progress,supported))
                with patch.object(game,"_load_maps",return_value=[(None,m)]), \
                     patch.object(pygame.event,"get",side_effect=events), \
                     patch.object(pygame.time,"Clock") as clock, \
                     patch.object(game,"draw_falling_block",side_effect=falling), \
                     patch.object(game,"_text",side_effect=text):
                    clock.return_value.tick.return_value=100
                    game.main()
                self.assertTrue(falls)
                self.assertTrue(messages)
                self.assertLess(falls[0][0],messages[0])
                self.assertGreaterEqual(falls[-1][2],1)
                self.assertEqual(falls[0][1]["mode"], "UPRIGHT" if upright else "HORIZONTAL")
                self.assertEqual(len(falls[0][3]),0 if upright else 1)

    def test_manual_switch_opens_then_closes_bridge_with_animation(self):
        m = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        visual = BridgeAnimator()
        frame = 0
        samples = []
        def events():
            nonlocal frame
            frame += 1
            if "b01" in visual.values:
                samples.append(visual.values["b01"])
            if frame == 1:
                return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                          pos=(game.WIDTH//2, game.HEIGHT//2-10))]
            if frame == 2:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
            if frame in (3, 19):
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)]
            if frame == 13:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)]
            return [pygame.event.Event(pygame.QUIT)] if frame >= 30 else []
        with patch.object(game, "_load_maps", return_value=[(None, m)]), \
             patch.object(game, "BridgeAnimator", return_value=visual), \
             patch.object(pygame.event, "get", side_effect=events), \
             patch.object(pygame.time, "Clock") as clock:
            clock.return_value.tick.return_value = 100
            game.main()
        self.assertIn(1, samples)
        self.assertTrue(any(0 < value < 1 for value in samples))
        self.assertEqual(samples[-1], 0)
        self.assertFalse(visual.busy)

    def test_small_cube_fall_uses_failed_destination_and_keeps_other_supported(self):
        grid = [["void"]*6 for _ in range(3)]
        grid[0][0]="floor"; grid[0][5]="goal"
        grid[1][1]=grid[1][3]="floor"
        m=parse_map({"schema_version":1,"id":"cube_fall","name":"cube fall",
                     "difficulty":"easy","rows":3,"cols":6,"grid":grid,"start":[0,0],
                     "bridges":[],"switches":[],"source":{"kind":"original","reference":"test"}})
        split=State("SPLIT",((1,1),(1,3)),1)
        frame=0;falls=[]
        def events():
            nonlocal frame
            frame+=1
            if frame==1:return [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,
                                                   pos=(game.WIDTH//2,game.HEIGHT//2-10))]
            if frame==2:return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)]
            if frame==3:return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT)]
            return [pygame.event.Event(pygame.QUIT)] if frame>=20 else []
        def falling(screen,state,camera,progress,action,supported):
            falls.append((state,progress,supported))
        with patch.object(game,"_load_maps",return_value=[(None,m)]), \
             patch.object(game,"initial_state",return_value=split), \
             patch.object(pygame.event,"get",side_effect=events), \
             patch.object(game,"draw_falling_block",side_effect=falling), \
             patch.object(pygame.time,"Clock") as clock:
            clock.return_value.tick.return_value=100
            game.main()
        self.assertTrue(falls)
        state,progress,supported=falls[-1]
        self.assertEqual(state["cells"][state["active"]],(1,4))
        self.assertEqual(supported,{(1,1)})
        self.assertEqual(progress,1)

    def test_split_animation_finishes_before_gui_commits_destination(self):
        m=load_map(ROOT / "data/maps/advanced_split_01.json")
        frame=0; moving=[]; resting=[]
        def events():
            nonlocal frame
            frame+=1
            if frame==1:return [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,
                                                   pos=(game.WIDTH//2,game.HEIGHT//2-10))]
            if frame==2:return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)]
            if frame in (3,10):return [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT)]
            return [pygame.event.Event(pygame.QUIT)] if frame>=24 else []
        def animated(screen,start,end,action,progress,camera):
            if end["mode"]=="SPLIT":moving.append((frame,progress))
        def block(screen,state,camera,**kwargs):
            if state["mode"]=="SPLIT":resting.append(frame)
        with patch.object(game,"_load_maps",return_value=[(None,m)]), \
             patch.object(pygame.event,"get",side_effect=events), \
             patch.object(game,"draw_animated_block",side_effect=animated), \
             patch.object(game,"draw_block",side_effect=block), \
             patch.object(pygame.time,"Clock") as clock:
            clock.return_value.tick.return_value=100
            game.main()
        self.assertGreater(len(moving),4)
        self.assertTrue(all(0 <= t < 1 for _,t in moving))
        self.assertGreater(resting[0],moving[-1][0])


if __name__ == "__main__":
    unittest.main()
