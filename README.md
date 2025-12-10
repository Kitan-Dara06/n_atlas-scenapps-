# N-Atlas Verbal Detection Service

Production-ready FastAPI service for video transcription, mention detection, and search.

## Features

- 🎤 **Video Transcription**: N-ATLAS ASR for Nigerian English
- 👥 **Mention Detection**: Detect user mentions in transcripts
- 🔍 **Search**: Fuzzy search through transcripts
- 🚀 **Production Ready**: Docker, proper logging, error handling

## Setup

### 1. Get Your Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with read access
3. Copy the token

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your token
# HF_TOKEN=hf_your_token_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Service

**Option A: Direct Python**
```bash
python main.py
```

**Option B: Docker**
```bash
docker-compose up --build
```

Service will be available at: `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Process Video
```bash
POST /process-video
Content-Type: application/json

{
  "video_path": "/path/to/video.mp4",
  "video_id": "vid_123",
  "users": [
    {
      "user_id": 1,
      "first_name": "Chinedu",
      "username": "nedu_codes"
    }
  ]
}
```

**Response:**
```json
{
  "video_id": "vid_123",
  "mentioned_user_ids": [1],
  "mentioned_users": [...],
  "mention_count": 1,
  "transcript": "full transcript text...",
  "duration_seconds": 125.4,
  "processed_at": "2024-01-15T10:30:00",
  "status": "success"
}
```

### Search Transcripts
```bash
POST /search
Content-Type: application/json

{
  "query": "climate",
  "transcripts": [
    {
      "video_id": "vid_1",
      "transcript": "Talk about climate change..."
    }
  ]
}
```

**Response:**
```json
{
  "query": "climate",
  "results": [
    {
      "video_id": "vid_1",
      "snippet": "...about climate change...",
      "match_count": 1,
      "relevance_score": 0.85
    }
  ],
  "total_results": 1
}
```

## Node.js Integration

```javascript
// Example: Process video
const response = await fetch('http://localhost:8000/process-video', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    video_path: '/uploads/video.mp4',
    video_id: 'vid_123',
    users: await getActiveUsers()  // From your DB
  })
});

const result = await response.json();

// Save transcript for search
await db.transcripts.insert({
  video_id: result.video_id,
  transcript: result.transcript,
  duration: result.duration_seconds
});

// Save mentions
for (const userId of result.mentioned_user_ids) {
  await db.mentions.insert({ video_id: result.video_id, user_id: userId });
}
```

```javascript
// Example: Search
const response = await fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'climate',
    transcripts: await db.transcripts.find({})  // All transcripts
  })
});

const results = await response.json();
// results.results contains matching videos
```

## Testing

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/test_mention.py -v
```

## Project Structure

```
n-atlas/
├── .env                    # Environment variables (DO NOT COMMIT)
├── .env.example            # Template
├── requirements.txt        # Dependencies
├── Dockerfile              # Docker config
├── docker-compose.yml      # Docker Compose config
├── config.py               # Settings
├── main.py                 # FastAPI app
├── models/
│   └── schemas.py          # Pydantic models
├── services/
│   ├── audio_extractor.py  # Audio extraction
│   ├── transcriber.py      # N-ATLAS transcription
│   ├── mention_detector.py # Mention detection
│   └── search.py           # Search service
├── utils/
│   └── logger.py           # Logging
└── tests/
    ├── test_mention.py     # Mention tests
    └── test_search.py      # Search tests
```

## Production Deployment

### Environment Variables

```bash
HF_TOKEN=your_token_here
N_ATLAS_MODEL=NCAIR1/NigerianAccentedEnglish
HOST=0.0.0.0
PORT=8000
DEBUG=False
TEMP_AUDIO_DIR=/app/temp_audio
LOG_LEVEL=INFO
```

### Docker Deployment

```bash
# Build
docker build -t n-atlas .

# Run
docker run -p 8000:8000 \
  -e HF_TOKEN=your_token \
  -v $(pwd)/temp_audio:/app/temp_audio \
  n-atlas
```

### Security Considerations

1. ✅ Never commit `.env` file
2. ✅ Use secrets management in production (AWS Secrets Manager, etc.)
3. ✅ Configure CORS properly (don't use `allow_origins=["*"]` in prod)
4. ✅ Add rate limiting
5. ✅ Add authentication/API keys

## Troubleshooting

### Issue: Model fails to load
**Solution**: Check your HF_TOKEN is valid and has access to the model

### Issue: Audio extraction fails
**Solution**: Ensure ffmpeg is installed (`apt-get install ffmpeg`)

### Issue: Out of memory
**Solution**: Reduce chunk size in transcriber.py or increase container memory

## License

[Your License]
"""
