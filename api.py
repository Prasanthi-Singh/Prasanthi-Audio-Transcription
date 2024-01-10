from flask import Flask, request, jsonify, make_response, g
from flask_restful import Resource, Api, reqparse
import whisper
import os
from functools import wraps

from werkzeug.utils import secure_filename
from pydub import AudioSegment
from collections import Counter
import re
import nltk

nltk.download('omw-1.4')
nltk.download('wordnet')
from nltk.tokenize import word_tokenize
from nltk import FreqDist
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask_cors import CORS
from flask_caching import Cache

app = Flask(__name__)
api = Api(app)

CORS(app)

model = whisper.load_model("base")

cred = credentials.Certificate("./voice-analyser-21f2001040-firebase-adminsdk-77b0d-d4a1954d5f.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

app.config["CACHE_TYPE"] = "SimpleCache"
app.config['CACHE_DEFAULT_TIMEOUT'] = 24 * 60 * 60
cache = Cache(app)

# Configuration for file upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def authentication_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # print(request.headers)
            access_token = dict(request.headers).get("User-Token")
            if not access_token:
                return make_response({"error_code": "TOKEN100", "error_message": "Id Token Missing"}, 404)
            user = auth.verify_id_token(access_token, check_revoked=True)
            g.user = user
            return func(*args, **kwargs)
        except auth.ExpiredIdTokenError:
            return make_response({"error_code": "USER101", "error_message": "Your session has expired. Kindly log in again."}, 401)
        except auth.InvalidIdTokenError:
            return make_response({"error_code": "USER100", "error_message": "Invalid Request"}, 401)
        except auth.UserNotFoundError:
            return make_response({"error_code": "USER100", "error_message": "Invalid Request.No User Found"}, 401)

    return wrapper


# In-memory database to store uploaded files
uploaded_files = []

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class FileTranscription(Resource):
    @authentication_required
    def post(self):
        try:
            # Get the file and uid from the request
            file = request.files['file']
            uid = request.form.get('uid')
            # print(file)

            # Save the file with a secure filename
            file_name = secure_filename(file.filename)
            file_path = os.path.join("uploads", file_name)
            file.save(file_path)

            # Print file name and size
            # print(file_si÷ze)
            file_size = os.path.getsize(file_path)
            # print(f"File Name: {file_name}, File Size: {file_size} bytes")

            # Load the Whisper ASR model

            # Transcribe the audio content of the file
            result = model.transcribe(file_path, task='translate')

            # Get the transcribed text
            transcribed_text = result["text"]
            # print(f"Transcribed Text: {transcribed_text}")

            db.collection('userData').document(g.user.get('uid')).collection('transcriptions').add({
                'transcribed text': transcribed_text,
                'created_at': firestore.SERVER_TIMESTAMP
            })

            cache.clear()

            return {'message': transcribed_text}, 200
        except Exception as e:
            # print(f"Error processing file: {str(e)}")
            return {'error': 'Failed to process file'}, 500


class TranscriptList(Resource):
    @authentication_required
    @cache.memoize(24*60*60)
    def get(self):
        try:
            # Fetch transcripts for the given uid
            # print(g.user)
            query = db.collection('userData').document(g.user.get('uid'))
            if query.get().exists:
                query = query.collection('transcriptions').stream()
            else:
                db.collection('userData').document(g.user.get('uid')).set({'created_at':firestore.SERVER_TIMESTAMP})
                query=[]
            transcripts_list = [{
                'id':doc.id,
                "data":{
                    'text':doc.to_dict().get('transcribed text')
                }
            } for doc in query]
            return {'transcripts': transcripts_list}, 200
        except Exception as e:
            # print(e)
            return {'error': 'Failed to fetch transcripts'}, 500

class Test(Resource):
    @authentication_required
    def get(self):
        return jsonify(message="HEYYY")


def get_transcripts():
    query = db.collection('userData').document(g.user.get('uid'))
    if query.get().exists:
        query = query.collection('transcriptions').stream()
    else:
        db.collection('userData').document(g.user.get('uid')).set({'created_at':firestore.SERVER_TIMESTAMP})
        query=[]
    transcripts_list = [doc.to_dict().get('transcribed text') for doc in query]
    # transcripts = db.session.query(Transcripts).filter_by(user_id=uid).all()
    # print('1')
    return transcripts_list


def analyze_text(transcripts):
    # print(transcripts)
    all_text = ' '.join([transcript for transcript in transcripts])

    all_words = []
    all_phrases = []

    # Initialize WordNet Lemmatizer
    lemmatizer = WordNetLemmatizer()
    print(all_text, 'yes')
    # Tokenize the transcript into words
    words = word_tokenize(all_text.lower())  # Assuming transcript is in the first column
    # print(words)
    # Lemmatize words
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

    all_words.extend(lemmatized_words)

    # Create phrases (n-grams)
    phrases = [f"{words[i]} {words[i + 1]} {words[i + 2]} {words[i + 3]} {words[i + 4]}" for i in range(len(lemmatized_words) - 5)]
    all_phrases.extend(phrases)

    # Remove stop words
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in all_words if word.isalnum() and word not in stop_words]

    # Count the frequency of words and phrases
    word_freq = FreqDist(filtered_words)
    phrase_freq = FreqDist(all_phrases)

    # Get the most frequent 3 words and phrases
    phrases = []
    most_words = word_freq.most_common(3)
    most_phrases = phrase_freq.most_common(3)
    words = [word for word, _ in most_words]
    phrases = [phrase for phrase, _ in most_phrases]

    return words, phrases


class FrequentWords(Resource):
    @cache.memoize(24*60*60)
    @authentication_required
    def get(self):
        transcripts = get_transcripts()
        # print(transcripts)
        if not transcripts:
            return jsonify({"error": f"No transcripts found for user"}), 404

        words, phrases = analyze_text(transcripts)
        result = {
            "frequent_words": words,
            "frequent_phrases": phrases,
        }
        return jsonify(result)

@app.route('/')
def hello_world():
    return "Hello World"

api.add_resource(FrequentWords, '/frequentwords')
api.add_resource(FileTranscription, '/transcribe')
api.add_resource(TranscriptList, '/transcripts')
api.add_resource(Test,'/test')

if __name__ == '__main__':
    app.run(debug=True)
