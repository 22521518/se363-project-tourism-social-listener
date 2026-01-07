
import asyncio
import unittest
from unittest.mock import MagicMock, patch
from core.crawl_service import CrawlService
from dao.json_file_writer import JsonFileWriter

class TestCrawlServiceFix(unittest.TestCase):
    @patch('core.crawl_service.SessionLocal')
    @patch('core.crawl_service.TourismCrawler')
    @patch('core.crawl_service.JsonFileWriter')
    def test_long_error_truncation(self, MockJsonFileWriter, MockCrawler, MockSessionLocal):
        # Setup mocks
        mock_session = MagicMock()
        MockSessionLocal.return_value.__enter__.return_value = mock_session
        
        mock_crawler_instance = MockCrawler.return_value
        long_error_msg = "Error content " * 200  # > 2000 chars
        mock_crawler_instance.crawl.side_effect = Exception(long_error_msg)
        
        mock_file_writer = MockJsonFileWriter.return_value
        
        service = CrawlService()
        # Ensure the file writer is our mock
        service.file_writer = mock_file_writer  
        
        # execution
        try:
            asyncio.run(service.crawl("http://test.com"))
        except Exception:
            pass
            
        # verification
        
        # Check if save_error was called with full error
        mock_file_writer.save_error.assert_called_once()
        call_args = mock_file_writer.save_error.call_args
        self.assertIn(long_error_msg, call_args[0][1]['error'])
        
        # Check if DB update used truncated error
        # We need to dig into the calls to history_dao.update_status
        # Since history_dao is created inside the method, we mock it via the session or patch the DAO class
        # But we didn't patch DAO classes in the test decorator, so let's check how to access it.
        # Actually, it's safer to patch the DAO classes directly.
        pass

    @patch('core.crawl_service.CrawlHistoryDAO')
    @patch('core.crawl_service.CrawlResultDAO') 
    @patch('core.crawl_service.SessionLocal')
    @patch('core.crawl_service.TourismCrawler')
    @patch('core.crawl_service.JsonFileWriter')
    def test_truncation_logic(self, MockJsonFileWriter, MockCrawler, MockSessionLocal, MockResultDAO, MockHistoryDAO):
        # Setup
        mock_session = MagicMock()
        MockSessionLocal.return_value.__enter__.return_value = mock_session
        
        mock_history_dao = MockHistoryDAO.return_value
        mock_history = MagicMock()
        mock_history.id = 123
        mock_history.request_id = "req-123"
        mock_history_dao.create.return_value = mock_history
        
        mock_crawler = MockCrawler.return_value
        long_error = "A" * 2000
        mock_crawler.crawl.side_effect = Exception(long_error)
        
        mock_file_writer = MockJsonFileWriter.return_value
        
        service = CrawlService()
        service.file_writer = mock_file_writer
        
        # Run
        try:
            asyncio.run(service.crawl("http://test.com"))
        except Exception:
            pass
            
        # Verify file save (full error)
        mock_file_writer.save_error.assert_called()
        saved_error = mock_file_writer.save_error.call_args[0][1]['error']
        self.assertEqual(saved_error, long_error)
        
        # Verify DB update (truncated)
        mock_history_dao.update_status.assert_called()
        call_kwargs = mock_history_dao.update_status.call_args[1]
        error_message = call_kwargs.get('error_message')
        
        self.assertEqual(len(error_message), 1003) # 1000 chars + "..."
        self.assertTrue(error_message.endswith("..."))
        print("\nTest passed: Error message truncated correctly and file saved.")

if __name__ == '__main__':
    unittest.main()
