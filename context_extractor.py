from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from datetime import timedelta  # Fixed typo
from yt_dlp import YoutubeDL
class ContextExtractor:
    def __init__(self, url, target_timestamp=0, num_segments=20, context_window=10.0):
        self.url = url
        self.video_id = self.extract_youtube_video_id(url)
        if not self.video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")

        self.target_timestamp = target_timestamp
        self.num_segments = num_segments
        self.context_window = context_window
        self.transcript = self.fetch_transcript()
        self.metadata = self.extract_metadata()

    def extract_youtube_video_id(self,url):
        """Extract YouTube video ID from URL"""
        try:
            parsed_url = urlparse(self.url)
            if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
                query = parse_qs(parsed_url.query)
                return query.get("v", [None])[0]
            elif parsed_url.hostname == "youtu.be":
                return parsed_url.path[1:]
            return None
        except Exception as e:
            return None

    def extract_metadata(self):
        """Extract video metadata using pytube"""
        try:
            data = {}
            opts = {
                "quiet": True,
                "skip_download": True,
                "extract_info": True,
            }
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                data["title"] = info.get("title")
                data["author"] = info.get("uploader")
                data["description"] = str(info.get("description","")).strip()
                data["views"] = info.get("view_count")
            return data
        except Exception as e:
            return {"title": "Unknown", "author": "Unknown", "description": "", "length": "Unknown"}

    def fetch_transcript(self):
        """Fetch transcript using YouTube Transcript API"""
        try:
            ytt = YouTubeTranscriptApi()
            transcript = ytt.fetch(self.video_id)
            return transcript
        except Exception as e:
            return []

    def extract_context(self, target_timestamp=None):
        """Extract relevant context segments from transcript based on target timestamp"""
        if target_timestamp is not None:
            self.target_timestamp = target_timestamp

        if not self.transcript:
            return {
                'error': 'No transcript available for this video',
                'target_timestamp': self.target_timestamp,
                'selected_segments': [],
                'metadata': self.metadata
            }

        # Convert transcript to segments with timing info
        all_segments = []
        for snippet in self.transcript.snippets:
            segment = {
                'text': snippet.text,
                'start': snippet.start,
                'duration': snippet.duration,
                'end': snippet.start + snippet.duration,
                'distance_from_target': abs(snippet.start - self.target_timestamp)
            }
            all_segments.append(segment)

        if not all_segments:
            return {
                'error': 'No segments found in transcript',
                'target_timestamp': self.target_timestamp,
                'selected_segments': [],
                'metadata': self.metadata
            }


        all_segments.sort(key=lambda x: x['start'])

        relevant_segments = []
        for segment in all_segments:
            segment_center = segment['start'] + (segment['duration'] / 2)
            if abs(segment_center - self.target_timestamp) <= self.context_window:
                relevant_segments.append(segment)

        if not relevant_segments:
            all_segments.sort(key=lambda x: x['distance_from_target'])
            relevant_segments = all_segments[:self.num_segments * 2]


        relevant_segments.sort(key=lambda x: (x['distance_from_target'], x['start']))
        selected_segments = relevant_segments[:self.num_segments]


        selected_segments.sort(key=lambda x: x['start'])

        closest_segment = min(relevant_segments, key=lambda x: x['distance_from_target']) if relevant_segments else None

        return selected_segments

    def get_context_at_timestamp(self, timestamp):
        """Get context for a specific timestamp"""
        result = self.extract_context(timestamp)
        text = ""
        for i in result:
            text += i['text']
        return text.strip()

    def get_full_transcript_text(self):
        """Get full transcript as text"""
        if not self.transcript:
            return ""
        return ' '.join([snippet['text'] for snippet in self.transcript])
