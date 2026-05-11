import unittest

from ai_assistant_ui.qwen_chat.fresh_query_interpreter import _extract_structural_target_limit_seed
from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import _requested_top_n as composite_requested_top_n
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import _requested_top_n as kpi_requested_top_n
from ai_assistant_ui.qwen_chat.ranking_limit_parser import extract_requested_top_n


class RankingLimitParserContractTests(unittest.TestCase):
	def test_word_number_limits_are_structural_not_defaulted(self):
		self.assertEqual(extract_requested_top_n("Display the top five suppliers based on Accounts Payable.", default_limit=10), 5)
		self.assertEqual(extract_requested_top_n("List the seven highest-revenue products from last year.", default_limit=10), 7)
		self.assertEqual(extract_requested_top_n("Show the five leading customers by revenue.", default_limit=10), 5)

	def test_time_windows_are_not_misread_as_rank_limits(self):
		self.assertEqual(extract_requested_top_n("show the latest 7 days of sales", default_limit=0), 0)
		self.assertEqual(_extract_structural_target_limit_seed("show the last 12 months of sales"), 0)

	def test_runtime_limit_helpers_share_the_same_contract(self):
		message = "List the seven highest-revenue products from last year."
		self.assertEqual(_extract_structural_target_limit_seed(message), 7)
		self.assertEqual(kpi_requested_top_n(message), 7)
		self.assertEqual(composite_requested_top_n(message), 7)
		self.assertEqual(kpi_requested_top_n("Display the top five suppliers based on Accounts Payable."), 5)
		self.assertEqual(composite_requested_top_n("Display the top five suppliers based on Accounts Payable."), 5)


if __name__ == "__main__":
	unittest.main()
