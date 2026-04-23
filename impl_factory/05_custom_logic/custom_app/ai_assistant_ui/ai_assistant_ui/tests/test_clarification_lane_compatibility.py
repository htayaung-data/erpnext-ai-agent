import unittest


class TestClarificationLaneCompatibility(unittest.TestCase):
    def test_compatibility_module_reexports_live_lane_functions(self):
        try:
            from ai_assistant_ui.qwen_chat import clarification_lane as compatibility_lane
            from ai_assistant_ui.qwen_chat.lanes import clarification_lane as live_lane
        except ModuleNotFoundError as exc:
            if str(exc.name or '') == 'frappe':
                self.skipTest('frappe is not available in this host-side unittest environment')
            raise

        self.assertIs(
            compatibility_lane.build_pending_clarification_frontdoor_skip,
            live_lane.build_pending_clarification_frontdoor_skip,
        )
        self.assertIs(
            compatibility_lane.handle_pending_clarification_turn,
            live_lane.handle_pending_clarification_turn,
        )


if __name__ == "__main__":
    unittest.main()
