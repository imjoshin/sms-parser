# Google sheets
SHEET = "1iYKly1fCOEnR6QTgDwezQuDVaMe6TxN8RPklIzq91uE"
WORKSHEET_SENT = "sent"
WORKSHEET_REC = "received"

# output
OUTPUT_FOLDER = "output"
OUTPUT_COUNT_CSV = True
OUTPUT_WORDCLOUD = True
OUTPUT_SENTIMENT_CSV = True

# word cloud
WC_HEIGHT = 600
WC_WIDTH = 800
WC_BGCOLOR = "white"

# word filtering
MIN_WORD_LENGTH = 3
IGNORED_WORDS = [
    "the", "at", "there", "some", "my",
    "of", "be", "use", "her", "than",
    "and", "this", "an", "would", "first",
    "a", "have", "each", "make", "water",
    "to", "from", "which", "like", "been",
    "in", "or", "she", "him", "call",
    "is", "one", "do", "into", "who",
    "you", "had", "how", "time", "oil",
    "that", "by", "their", "has", "its",
    "it", "word", "if", "look", "now",
    "he", "but", "will", "two", "find",
    "was", "not", "up", "more", "long",
    "for", "what", "other", "write", "down",
    "on", "all", "about", "go", "day",
    "are", "were", "out", "see", "did",
    "as", "we", "many", "number", "get",
    "with", "when", "then", "no", "come",
    "his", "your", "them", "way", "made",
    "they", "can", "these", "could", "may",
    "I", "said", "so", "people", "part"
]

# sentiment analysis
SA_GRANULARITY = "hour" # hour or day

# other settings
MIN_TEXTS_TO_PROCESS = 100
