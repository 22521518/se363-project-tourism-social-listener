"""
Vietnamese text processor for ACSA.
Includes word segmentation, emoji processing, sentiment word normalization, etc.
"""
import re
import unicodedata
import string
from typing import Tuple, Set, Dict, Optional
from pathlib import Path

from .base import TextProcessor


class VietnameseTextProcessor(TextProcessor):
    """Vietnamese text processor with word segmentation."""
    
    VNCORENLP_URL = "https://github.com/vncorenlp/VnCoreNLP/archive/refs/tags/v1.2.zip"
    VNCORENLP_DIR = "VnCoreNLP-1.2"
    VNCORENLP_JAR = "VnCoreNLP-1.2.jar"
    
    def __init__(self, 
                 vncorenlp_path: Optional[str] = None,
                 sentiment_lexicon_path: Optional[str] = None):
        """
        Initialize Vietnamese text processor.
        
        Args:
            vncorenlp_path: Path to VnCoreNLP JAR file
            sentiment_lexicon_path: Path to VietSentiWordnet file
        """
        self.vncorenlp_path = vncorenlp_path
        self.sentiment_lexicon_path = sentiment_lexicon_path
        self._word_segmenter = None
        self._sentiment_lexicons = None
    
    def _download_vncorenlp(self, target_dir: Path) -> Optional[str]:
        """Download and extract VnCoreNLP if not present."""
        import urllib.request
        import zipfile
        import shutil
        
        target_dir.mkdir(parents=True, exist_ok=True)
        zip_path = target_dir / "vncorenlp.zip"
        extract_dir = target_dir / self.VNCORENLP_DIR
        jar_path = extract_dir / self.VNCORENLP_JAR
        
        if jar_path.exists():
            print(f"✅ VnCoreNLP already exists: {jar_path}")
            return str(jar_path)
        
        try:
            print(f"📥 Downloading VnCoreNLP from {self.VNCORENLP_URL}...")
            urllib.request.urlretrieve(self.VNCORENLP_URL, zip_path)
            
            print(f"📦 Extracting to {target_dir}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # The zip contains VnCoreNLP-1.2/VnCoreNLP-1.2/...
            inner_dir = target_dir / f"VnCoreNLP-{self.VNCORENLP_DIR.split('-')[1]}"
            if inner_dir.exists() and not extract_dir.exists():
                shutil.move(str(inner_dir), str(extract_dir))
            
            # Clean up
            zip_path.unlink()
            
            if jar_path.exists():
                print(f"✅ VnCoreNLP downloaded successfully: {jar_path}")
                return str(jar_path)
            else:
                print(f"⚠️ JAR not found after extraction at {jar_path}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to download VnCoreNLP: {e}")
            return None
        
    @property
    def word_segmenter(self):
        """Lazy load word segmenter (pyvi fallback)."""
        if self._word_segmenter is None:
            vncorenlp_path = self.vncorenlp_path
            
            # Try to find or download VnCoreNLP
            if not vncorenlp_path:
                # Check common locations
                possible_paths = [
                    Path("/opt/airflow/VnCoreNLP-1.2/VnCoreNLP-1.2.jar"),
                    Path.home() / "VnCoreNLP-1.2" / "VnCoreNLP-1.2.jar",
                    Path(__file__).parent.parent / "VnCoreNLP-1.2" / "VnCoreNLP-1.2.jar",
                ]
                for p in possible_paths:
                    if p.exists():
                        vncorenlp_path = str(p)
                        break
            
            if vncorenlp_path:
                try:
                    from vncorenlp import VnCoreNLP
                    self._word_segmenter = VnCoreNLP(
                        vncorenlp_path,
                        annotators="wseg",
                        quiet=True
                    )
                    print(f"✅ VnCoreNLP loaded from: {vncorenlp_path}")
                except Exception as e:
                    print(f"⚠️ Could not load VnCoreNLP: {e}")
                    print("Falling back to pyvi tokenizer")
                    self._word_segmenter = "pyvi"
            else:
                print("ℹ️ VnCoreNLP not found, using pyvi tokenizer")
                self._word_segmenter = "pyvi"
                
        return self._word_segmenter
    
    @property
    def sentiment_lexicons(self) -> Tuple[Set, Set, Set, Dict]:
        """Lazy load sentiment lexicons."""
        if self._sentiment_lexicons is None:
            self._sentiment_lexicons = self._load_sentiment_lexicon()
        return self._sentiment_lexicons
    
    def lowercase(self, text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()
    
    def remove_elongated_chars(self, text: str) -> str:
        """Remove elongated characters (e.g., đẹppppp -> đẹp)."""
        pattern = rf"(\w)\1+"
        text = re.sub(pattern, r'\1', text)
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        return unicodedata.normalize("NFC", text)
    
    def process_emojis(self, text: str) -> str:
        """Convert emojis to sentiment labels."""
        emojis_list = {
            "👹": "negative", "👻": "positive", "💃": "positive", '🤙': 'positive ',
            '👍': 'positive ', "💄": "positive", "💎": "positive", "💩": "positive",
            "😕": "negative", "😱": "negative", "😸": "positive", "😾": "negative",
            "🚫": "negative", "🤬": "negative", "🧚": "positive", "🧡": "positive",
            '🐶': 'positive ', '👎': 'negative ', '😣': 'negative ', '✨': 'positive ',
            '❣': 'positive ', '☀': 'positive ', '♥': 'positive ', '🤩': 'positive ',
            'like': 'positive ', ':))': 'positive ', ':)': 'positive ',
            'he he': 'positive ', 'hehe': 'positive ', 'hihi': 'positive ',
            'haha': 'positive ', 'hjhj': 'positive ', ' lol ': 'negative ',
            ' cc ': 'negative ', 'huhu': 'negative ', '><': 'positive ',
            '💌': 'positive ', '🥰': 'positive ', '🙆': 'positive ', '😅': 'negative ',
            '🤒': 'negative ', '🤨': 'negative ', '🤦': 'negative ', '😬': 'negative ',
            '🔋': 'positive ', '💔': 'negative ', '🤮': 'negative ', '✋': 'positive ',
            '🤣': 'positive ', '🖤': 'positive ', '🤤': 'positive ', ':(': 'negative ',
            '😢': 'negative ', '❤': 'positive ', '😍': 'positive ', '😘': 'positive ',
            '😪': 'negative ', '😊': 'positive ', '?': ' ? ', '😁': 'positive ',
            '💖': 'positive ', '😟': 'negative ', '😭': 'negative ', '💯': 'positive ',
            '💗': 'positive ', '♡': 'positive ', '💜': 'positive ', '🤗': 'positive ',
            '^^': 'positive ', '😨': 'negative ', '☺': 'positive ', '💋': 'positive ',
            '👌': 'positive ', '😖': 'negative ', '😀': 'positive ', ':((': 'negative ',
            '😡': 'negative ', '😠': 'negative ', '😒': 'negative ', '🙂': 'positive ',
            '😏': 'negative ', '😝': 'positive ', '😄': 'positive ', '😙': 'positive ',
            '😤': 'negative ', '😎': 'positive ', '😆': 'positive ', '💚': 'positive ',
            '✌': 'positive ', '💕': 'positive ', '😞': 'negative ', '😓': 'negative ',
            '️🆗️': 'positive ', '😉': 'positive ', '😂': 'positive ', ':v': 'positive ',
            '=))': 'positive ', '😋': 'positive ', '💓': 'positive ', '😐': 'negative ',
            ':3': 'positive ', '😫': 'negative ', '😥': 'negative ', '😃': 'positive ',
            '😌': ' 😌 ', '💛': 'positive ', '🤝': 'positive ', '🎈': 'positive ',
            '😗': 'positive ', '🤔': 'negative ', '😑': 'negative ', '🔥': 'negative ',
            '🙏': 'negative ', '🆗': 'positive ', '😻': 'positive ', '💙': 'positive ',
            '💟': 'positive ', '😚': 'positive ', '❌': 'negative ', '👏': 'positive ',
            ';)': 'positive ', '<3': 'positive ', '🌝': 'positive ', '🌷': 'positive ',
            '🌸': 'positive ', '🌺': 'positive ', '🌼': 'positive ', '🍓': 'positive ',
            '🐅': 'positive ', '🐾': 'positive ', '👉': 'positive ', '💐': 'positive ',
            '💞': 'positive ', '💥': 'positive ', '💪': 'positive ', '💰': 'positive ',
            '😇': 'positive ', '😛': 'positive ', '😜': 'positive ', '🙃': 'negative ',
            '🤑': 'positive ', '🤪': 'positive ', '☹': 'negative ', '💀': 'negative ',
            '😔': 'negative ', '😧': 'negative ', '😩': 'negative ', '😰': 'negative ',
            '😳': 'negative ', '😵': 'negative ', '😶': 'negative ', '🙁': 'negative ',
            '🎉': 'positive '
        }
        for emoji, label in emojis_list.items():
            text = text.replace(emoji, f'EMO{label.upper()}')
        text = ' '.join(text.split())
        return text
    
    def normalize_sentiment_words(self, text: str) -> str:
        """Normalize common Vietnamese sentiment words and abbreviations."""
        sentiment_word_map = {
            'ô kêi': ' ok ', 'okie': ' ok ', ' o kê ': ' ok ',
            'okey': ' ok ', 'ôkê': ' ok ', 'oki': ' ok ', ' oke ': ' ok ',
            ' okay': ' ok ', 'okê': ' ok ',
            ' tks ': ' cám ơn ', 'thks': ' cám ơn ', 'thanks': ' cám ơn ',
            'ths': ' cám ơn ', 'thank': ' cám ơn ',
            '⭐': 'star ', '*': 'star ', '🌟': 'star ',
            'kg ': ' không ', 'not': ' không ', ' kg ': ' không ',
            '"k ': ' không ', ' kh ': ' không ', 'kô': ' không ',
            'hok': ' không ', ' kp ': ' không phải ', ' kô ': ' không ',
            '"ko ': ' không ', ' ko ': ' không ', ' k ': ' không ',
            'khong': ' không ', ' hok ': ' không ',
            'cute': ' dễ thương ', ' vs ': ' với ', 'wa': ' quá ',
            'wá': ' quá', 'j': ' gì ', '"': ' ',
            ' sz ': ' cỡ ', 'size': ' cỡ ', ' đx ': ' được ',
            'dk': ' được ', 'dc': ' được ', 'đk': ' được ', 'đc': ' được ',
            'authentic': ' chuẩn chính hãng ', ' aut ': ' chuẩn chính hãng ',
            ' auth ': ' chuẩn chính hãng ', 'store': ' cửa hàng ',
            'shop': ' cửa hàng ', 'sp': ' sản phẩm ', 'gud': ' tốt ',
            'god': ' tốt ', 'wel done': ' tốt ', 'good': ' tốt ',
            'gút': ' tốt ', 'sấu': ' xấu ', 'gut': ' tốt ', ' tot ': ' tốt ',
            ' nice ': ' tốt ', 'perfect': 'rất tốt', 'bt': ' bình thường ',
            'time': ' thời gian ', 'qá': ' quá ', ' ship ': ' giao hàng ',
            ' m ': ' mình ', ' mik ': ' mình ', 'ể': 'ể',
            'product': 'sản phẩm', 'quality': 'chất lượng', 'chat': ' chất ',
            'excelent': 'hoàn hảo', 'bad': 'tệ', 'fresh': ' tươi ', 'sad': ' tệ ',
            'date': ' hạn sử dụng ', 'hsd': ' hạn sử dụng ',
            'quickly': ' nhanh ', 'quick': ' nhanh ', 'fast': ' nhanh ',
            'delivery': ' giao hàng ', ' síp ': ' giao hàng ',
            'beautiful': ' đẹp tuyệt vời ', ' tl ': ' trả lời ', ' r ': ' rồi ',
            ' shopE ': ' cửa hàng ', ' order ': ' đặt hàng ',
            'chất lg': ' chất lượng ', ' sd ': ' sử dụng ', ' dt ': ' điện thoại ',
            ' nt ': ' nhắn tin ', 'sài': ' xài ', 'bjo': ' bao giờ ',
            'thick': ' thích ', 'thik': ' thích ', ' sop ': ' cửa hàng ',
            ' fb ': ' facebook ', ' face ': ' facebook ', ' very ': ' rất ',
            'quả ng ': ' quảng  ', 'dep': ' đẹp ', ' xau ': ' xấu ',
            'delicious': ' ngon ', 'hàg': ' hàng ', 'qủa': ' quả ',
            'iu': ' yêu ', 'fake': ' giả mạo ', 'trl': 'trả lời',
            ' por ': ' tệ ', ' poor ': ' tệ ', 'ib': ' nhắn tin ',
            'rep': ' trả lời ', 'fback': ' feedback ', 'fedback': ' feedback '
        }
        for word, replacement in sentiment_word_map.items():
            text = text.replace(word, replacement)
        return text
    
    def remove_punctuation(self, text: str) -> str:
        """Remove punctuation from text."""
        translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
        return text.translate(translator)
    
    def _load_sentiment_lexicon(self) -> Tuple[Set, Set, Set, Dict]:
        """Load sentiment lexicon from VietSentiWordnet file or default sets."""
        not_words = {
            "không", 'không_hề', "chẳng", "chưa", "không_phải", "chả", "mất",
            "thiếu", "vô", "đếch", "đéo", "kém", "nỏ", "not",
            "bớt", "không_bao_giờ",
        }
        
        positive_words = {
            "ưng_ý", "ưng", "kỹ", "được", "ô_kê", "ok", "mịn", "ổn", "xinh",
            "chúc_mừng", "hạnh_phúc", "sang", "oách", "khen", "ổn_định",
            "cảm_ơn", "cám_ơn", "chuẩn", "hoàn_thiện", "chắc_chắn", "sạch_sẽ",
            "hài_lòng", "chất_lượng", "hấp_dẫn", "vui_vẻ", "nguyên_chất",
            "thuận_lợi", "có_lợi", "tích_cực", "khuyến_khích", "tốt_hơn",
            "vị_tha", "sắc", "bén", "thích_hợp", "quý_báu", "sâu_sắc",
            "thịnh_vượng", "xinh_đẹp", "rực_rỡ", "trong_sáng", "chấp_nhận_được",
            "khéo_léo", "nghệ_thuật", "yên_tâm", "uyển_chuyển", "sôi_động",
            "nhân_đạo", "thân_mật", "thoải_mái", "đặc_biệt", "toàn_diện",
            "hòa_đồng", "hài_hòa", "thuận_tiện", "lịch_sự", "may_mắn", "may",
            "đoan_trang", "phấn_chấn", "sành_điệu", "sáng_suốt", "kín_đáo",
            "mát_mẻ", "lấp_lánh", "danh_dự", "dễ_dàng", "say_mê", "nhiệt_tình",
            "đạo_đức", "trung_thực", "trung_thành", "chung_thủy", "ngon",
            "chu_đáo", "ngăn_nắp", "lành_mạnh", "hợp_vệ_sinh", "khôn",
            "khen_ngợi", "quý_giá", "kháng_khuẩn", "êm_tai", "tinh_túy",
            "du_dương", "bổ_ích", "hồng_hào", "khỏe_khoắn", "khỏe_mạnh",
            "khỏe", "mạnh", "săn_chắc", "sung_sức", "mạnh_khỏe", "trẻ_trung",
            "đùa", "đề_cao", "quản_lý", "cánh_tay_phải", "nhận_dạng_được",
            "hoàn_hảo", "trọn_vẹn", "lý_tưởng", "dễ_an_ủi", "đẹp", "duyên_dáng",
            "tuyệt_vời", "đáng_ngưỡng_mộ", "thú_vị", "ngọt_ngào", "lạc_quan",
            "sinh_lợi", "chính_đáng", "khiêm_tốn", "minh_mẫn", "uy_tín",
            "vinh_dự", "thẳng_thắn", "bảo_đảm", "màu_mỡ", "dễ_chịu", "tươi",
            "cẩn_thận", "đúng", "hiệu_quả", "cute", "dễ_thương", "phê", "xịn",
            "sịn", "vui_tính", "chính_hãng", "thực_sự", "vinh_quang",
            "thánh_thiện", "vui_tươi", "gợi_cảm", "cân_đối", "chân_thành",
            "thành_thạo", "tinh_tế", "kiên_cố", "thân_thiện", "thích",
            "tỏa_sáng", "ngưỡng_mộ", "phù_hợp", "hy_vọng", "tốt_đẹp", "tốt",
            "giỏi_giang", "lôi_cuốn", "uyên_bác", "yêu", "thích_thú", "ái_ân",
            "chân_tình", "chăm_chút", "tuyệt", "nhẹ_nhõm", "xinh_xắn", "giỏi",
            "khủng", "đạt", "hợp_lý", "hợp_lí", "sạch", "ấm", "mềm",
            "cải_thiện", "tiện", "gọn", "tin_tưởng", "nhạy", "nhạy_bén",
            "pin_rất_trâu", "bao_mượt", "pin_trâu", "sạc_nhanh"
        }
        
        negative_words = {
            "bất_lợi", "chán", "chật_hẹp", "chật", "tức_giận", "xấu",
            "khủng_khiếp", "mỏng", "nhầm", "đe_dọa", "ghê", "hiểm_ác",
            "lừa_dối", "lừa", "mặn", "tệ_nhất", "bẩn_thỉu", "hà_khắc",
            "cay", "ngu_dốt", "hiếm", "ngược_đãi", "chậm", "căng_thẳng",
            "thô_bạo", "khó_chịu", "khắc_nghiệt", "kị", "ghen", "hỗn_tạp",
            "dơ", "liều_lĩnh", "dơ_bẩn", "thô_tục", "tệ_hại", "tệ",
            "nhầm_lẫn", "quá_mức", "xấu_số", "ngu_si", "đau_đớn", "phàn_nàn",
            "phản_cảm", "tàn_phá", "bất_mãn", "hung_hăng", "bất_tiện",
            "hoang_sơ", "giả_dối", "đắt_đỏ", "đắt", "yếu", "sai_lầm", "lầm",
            "nghiêm_trọng", "đáng_ghét", "hỏng", "bất_hợp_tác", "chán_nản",
            "yếu_đuối", "trục_trặc", "bực_bội", "tàn_bạo", "bừa_bãi",
            "lăng_nhăng", "thất_vọng", "chê_bai", "loang_lổ", "tiêu_hao",
            "bất_công", "lang_thang", "khổ_sở", "vớ_vẩn", "bất_hạnh",
            "vô_tâm", "bù_xù", "bừa_bộn", "khó", "gian_dối", "vô_dụng",
            "vô_nghĩa", "ác", "chóng_mặt", "là_lạ", "miễn_cưỡng", "ngu_ngốc",
            "dị_ứng", "co_cứng", "hại", "lạm_dụng", "vu_khống", "tai_hại",
            "tồi", "xảo_quyệt", "đau_thương", "hỗn_loạn", "nhức_nhối",
            "đỏ_ngầu", "loét", "sưng_tấy", "tấy", "viêm", "ốm_yếu", "khô",
            "nặng_bụng", "nặng_nề", "khàn_khàn", "dị", "lật", "vô_vọng",
            "gian_lận", "xuống_cấp", "ứ_đọng", "lạnh_toát", "oi_ả", "sưng",
            "bị_nhọt", "có_ác_cảm", "tàn_nhẫn", "mù_quáng", "bất_thường",
            "bất_tín", "gay_gắt", "mất_lòng", "bạc_bẽo", "thô", "thất_sách",
            "quái_đản", "thù_địch", "xúc_phạm", "bất_trị", "run", "gây_mê",
            "cạn_kiệt", "tàn_tật", "định_mệnh", "hôi_thối", "mốc", "hôi",
            "gẫy", "lởm", "hắc", "dỏm", "giởm", "dởm", "nhòe", "chết", "móp",
            "mùi_thối", "thối", "ràng_buộc", "hư_hỏng", "bị", "hư", "giả_mạo",
            "giả_tạo", "giả", "sợ_hãi", "khó_khăn", "bốc_mùi", "dã_man",
            "nham_hiểm", "tham_nhũng", "xấu_xa", "ủ_rũ", "thâm", "kích_ứng",
            "hờn_dỗi", "bôi_nhọ", "tác_hại", "tinh_nghịch", "khó_tiêu",
            "thong_thả", "nhàn_nhã", "trơ", "thối_rữa", "phù_phiếm",
            "độc_quyền", "do_dự", "nạn_nhân", "rắc_rối", "sai", "định_kiến",
            "buồn_bã", "bứt_rứt", "mùi", "bại_hoại", "giận_dữ", "báo_động",
            "phẫn_nộ", "ghét", "kênh_kiệu", "nhàm_chán", "buồn", "xót_xa",
            "đau_lòng", "1star", "2star", "ngắn", "tổn_thất", "bức_xúc",
            "tàn_ác", "ác_hiểm", "rởm", "tróc", "ám_sát", "lười", "vụn",
            "gãy", "hối_tiếc", "tiêu_cực", "ngu", "hốt_hoảng", "đểu", "nhái",
            "ngứa", "cùi", "hàng_lô", "hàng_giả", "phức_tạp", "nát", "mờ",
            "đơ", "ngỏm", "lâu", "nặng", "thủng", "trầy", "dão", "lỗi",
            "kém", "lùn", "bùn", "thiếu", "rách", "ngấy", "tồi_tệ", "mẻ",
            "ẩu", "cẩu_thả", "lộn", "ế_ẩm", "ế", "sướt", "tốn_pin",
            "nóng_máy", "nóng", "giật_lag"
        }
        
        sentiment_lexicon = {}
        
        # Try to load from bundled VietSentiWordnet file
        lexicon_path = self.sentiment_lexicon_path
        if not lexicon_path:
            # Check bundled file location
            bundled_path = Path(__file__).parent / "VietSentiWordnet_ver1.0.txt"
            if bundled_path.exists():
                lexicon_path = str(bundled_path)
        
        if lexicon_path and Path(lexicon_path).exists():
            try:
                with open(lexicon_path, "r", encoding="utf-8") as file:
                    header_skipped = False
                    for line in file:
                        if not header_skipped:
                            if "POS\tID\tPosScore\tNegScore\tSynsetTerms\tGloss" in line:
                                header_skipped = True
                            continue
                        parts = line.strip().split("\t")
                        if len(parts) >= 5:
                            word = parts[4]
                            pos_score = float(parts[2])
                            neg_score = float(parts[3])
                            word_clean = word.split('#')[0]
                            if pos_score > 0.5:
                                sentiment_lexicon[word_clean] = "positive"
                                positive_words.add(word_clean)
                            if neg_score > 0.5:
                                sentiment_lexicon[word_clean] = "negative"
                                negative_words.add(word_clean)
                print(f"✅ Loaded {len(sentiment_lexicon)} words from VietSentiWordnet")
            except Exception as e:
                print(f"⚠️ Could not load sentiment lexicon: {e}")
        
        # Add predefined words to lexicon
        for word in positive_words:
            if word not in sentiment_lexicon:
                sentiment_lexicon[word] = "positive"
        for word in negative_words:
            if word not in sentiment_lexicon:
                sentiment_lexicon[word] = "negative"
        
        return not_words, positive_words, negative_words, sentiment_lexicon
    
    def handle_negation(self, text: str) -> str:
        """Handle negation patterns in text."""
        text = self.remove_punctuation(text)
        not_words, positive_words, negative_words, _ = self.sentiment_lexicons
        
        try:
            from pyvi import ViTokenizer
            text = ViTokenizer.tokenize(text)
        except ImportError:
            pass
        
        texts = text.split()
        len_text = len(texts)
        
        i = 0
        while i < len_text:
            cp_text = texts[i]
            if cp_text in not_words and i < len_text - 1:
                next_word = texts[i + 1]
                if next_word in positive_words:
                    texts[i] = 'NOTPOS'
                    texts[i + 1] = ''
                elif next_word in negative_words:
                    texts[i] = 'NOTNEG'
                    texts[i + 1] = ''
            i += 1
        
        return ' '.join(filter(None, texts))
    
    def clean_text(self, text: str) -> str:
        """Full text cleaning pipeline."""
        if not isinstance(text, str):
            return ""
        
        text = self.lowercase(text)
        text = self.process_emojis(text)
        text = self.remove_elongated_chars(text)
        text = self.normalize_unicode(text)
        text = self.normalize_sentiment_words(text)
        text = self.handle_negation(text)
        text = self.remove_punctuation(text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def tokenize(self, text: str) -> str:
        """Tokenize text using pyvi or VnCoreNLP."""
        if not text.strip():
            return ""
        
        if self.word_segmenter == "pyvi":
            try:
                from pyvi import ViTokenizer
                return ViTokenizer.tokenize(text)
            except ImportError:
                return text
        else:
            try:
                tokens = self.word_segmenter.tokenize(text)
                return ' '.join(sum(tokens, []))
            except Exception:
                return text
    
    def close(self):
        """Close VnCoreNLP and forcefully kill the Java subprocess."""
        if self._word_segmenter and self._word_segmenter != "pyvi":
            try:
                # First try the standard close method
                self._word_segmenter.close()
                print("✅ VnCoreNLP close() called")
            except Exception as e:
                print(f"⚠️ Error during VnCoreNLP close(): {e}")
            
            # Forcefully kill the Java subprocess if it exists
            try:
                if hasattr(self._word_segmenter, '_process') and self._word_segmenter._process:
                    proc = self._word_segmenter._process
                    if proc.poll() is None:  # Still running
                        print(f"🔪 Forcefully killing VnCoreNLP Java process (PID: {proc.pid})...")
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                            print("✅ VnCoreNLP process terminated gracefully")
                        except:
                            # Force kill if terminate doesn't work
                            proc.kill()
                            proc.wait()
                            print("✅ VnCoreNLP process killed forcefully")
            except Exception as e:
                print(f"⚠️ Error killing VnCoreNLP process: {e}")
            
            # Clear the reference
            self._word_segmenter = None
            print("✅ VnCoreNLP resources released")