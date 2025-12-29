# YouTube Channel Management - Console Script

Script console để quản lý việc thêm channel YouTube vào hệ thống tracking.

## Cấu trúc thư mục

```
web/
├── streamlit/           # Streamlit web application
│   └── streamlit_app.py
└── dev/                 # Development console scripts
    ├── add_channel.py   # Script để thêm channel mới
    ├── requirements.txt # Dependencies
    └── README.md        # File này
```

## Yêu cầu

- Python 3.7+
- PostgreSQL database đang chạy
- Environment variables được cấu hình (.env file)

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Đảm bảo file `.env` đã được cấu hình với database credentials:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=airflow
DB_PASSWORD=airflow
DB_NAME=airflow
```

## Cách sử dụng

### Thêm channel mới

```bash
python add_channel.py <channel_id>
```

**Ví dụ:**
```bash
python add_channel.py UC_x5XG1OV2P6uZZ5FSM9Ttw
```

### Tìm YouTube Channel ID

1. Truy cập channel YouTube
2. Click chuột phải vào trang và chọn "View Page Source"
3. Tìm `"channelId"` hoặc `"externalId"` trong source code
4. Hoặc sử dụng URL dạng: `https://www.youtube.com/channel/<CHANNEL_ID>`

## Output mẫu

```
============================================================
📺 YouTube Channel Tracker - Add New Channel
============================================================

🔄 Adding channel UC_x5XG1OV2P6uZZ5FSM9Ttw...
✅ Success! Channel UC_x5XG1OV2P6uZZ5FSM9Ttw added and tracked successfully!
   Data will appear after the ingestion process runs.

============================================================
```

## Xử lý lỗi

### Import Error
```
❌ Import Error: No module named 'projects.services.ingestion.youtube.config'
```
**Giải pháp:** Đảm bảo bạn đang chạy script từ đúng thư mục và đã cài đặt dependencies.

### Configuration Error
```
❌ Configuration Error: Missing required environment variable
```
**Giải pháp:** Kiểm tra file `.env` và đảm bảo tất cả biến môi trường cần thiết đã được cấu hình.

### Database Connection Error
```
❌ Failed to add channel: could not connect to server
```
**Giải pháp:** Đảm bảo PostgreSQL database đang chạy và credentials trong `.env` là chính xác.

## So sánh với Streamlit UI

| Feature | Console Script | Streamlit UI |
|---------|---------------|--------------|
| Thêm channel | ✅ | ✅ |
| Xóa channel | ❌ | ✅ |
| Xem danh sách | ❌ | ✅ |
| Xem thống kê | ❌ | ✅ |
| Automation | ✅ (scripting) | ❌ |
| Batch processing | ✅ | ❌ |

## Sử dụng nâng cao

### Thêm nhiều channels từ file

Tạo file `channels.txt`:
```
UC_x5XG1OV2P6uZZ5FSM9Ttw
UCYfdidRxbB8Qhf0Nx7ioOYw
UCsT0YIqwnpJCM-mx7-gSA4Q
```

Chạy script với loop:
```bash
for channel in $(cat channels.txt); do
    python add_channel.py $channel
done
```

## Lưu ý

- Script này chỉ đăng ký channel vào database
- Data thực tế sẽ được thu thập bởi background workers/Airflow DAGs
- Kiểm tra Streamlit UI để xem data sau khi workers đã chạy
