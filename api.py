from flask import Flask, request , jsonify , make_response , g
from flask_restful import Resource, Api, reqparse
import whisper
import os
from functools import wraps

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from database import User , Transcripts
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
from firebase_admin import credentials , auth
from flask_cors import CORS
from flask_caching import Cache


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:prasanthi@localhost:5433/kyro'
db = SQLAlchemy(app)
api = Api(app)
CORS(app)


cred = credentials.Certificate("./prasanthi-kyro-project-firebase-adminsdk-jo6lc-ee73cc4ccb.json")
firebase_admin.initialize_app(cred)


app.config["CACHE_TYPE"] = "SimpleCache"
app.config['CACHE_DEFAULT_TIMEOUT'] = 24 * 60 * 60
cache= Cache(app)

# Configuration for file upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def authentication_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
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
        print('chutiya pro')
        try:
            print('chutiya')
            # Get the file and uid from the request
            file = request.files['file']
            uid = request.form.get('uid')
            print(file)

            # Save the file with a secure filename
            file_name = secure_filename(file.filename)
            file_path = os.path.join("uploads", file_name)
            file.save(file_path)

            # Print file name and size
            # print(file_si÷ze)
            file_size = os.path.getsize(file_path)
            print(f"File Name: {file_name}, File Size: {file_size} bytes")

            # Load the Whisper ASR model
            model = whisper.load_model("base")

            # Transcribe the audio content of the file
            result = model.transcribe(file_path, task='translate')

            # Get the transcribed text
            transcribed_text = result["text"]
            print(f"Transcribed Text: {transcribed_text}")

            # Store uid and transcribed_text in the database
            new_transcript = Transcripts(user_id=uid, transcript=transcribed_text)
            db.session.add(new_transcript)
            db.session.commit()
            cache.clear()

            return {'message': transcribed_text}, 200
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return {'error': 'Failed to process file'}, 500


class TranscriptList(Resource):
    @cache.memoize(timeout=24*60*60)
    def get(self, uid):
        print('yes')
        try:
            # Fetch transcripts for the given uid
            transcripts = db.session.query(Transcripts).filter_by(user_id=uid).all()


            # Transform transcripts to a list of dictionaries
            transcripts_list = [
                {
                    'transcript_id': transcript.transcript_id,
                    'transcript': transcript.transcript,
                    'created_at': transcript.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for transcript in transcripts
            ]

            return {'transcripts': transcripts_list}, 200
        except Exception as e:
            print(f"Error fetching transcripts: {str(e)}")
            return {'error': 'Failed to fetch transcripts'}, 500
        
def get_transcripts(uid):
    transcripts = db.session.query(Transcripts).filter_by(user_id=uid).all()
    print('1')
    return transcripts


def analyze_text(transcripts):
    all_text = ' '.join([transcript.transcript for transcript in transcripts])

    all_words = []
    all_phrases = []

# Initialize WordNet Lemmatizer
    lemmatizer = WordNetLemmatizer()
    print(all_text , 'yes')
    # Tokenize the transcript into words
    words = word_tokenize(all_text.lower())  # Assuming transcript is in the first column
        # print(words)
        # Lemmatize words
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
        
    all_words.extend(lemmatized_words)

        # Create phrases (n-grams)
    phrases = [f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]} {words[i+4]}" for i in range(len(lemmatized_words)-5)]
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
    print(words)
    return words, phrases



class FrequentWords(Resource):
    def get(self, user_id):
        transcripts = get_transcripts(user_id)

        if not transcripts:
            return jsonify({"error": f"No transcripts found for user with ID {user_id}"}), 404

        words, phrases = analyze_text(transcripts)
        result = {
            "frequent_words": words,
            "frequent_phrases": phrases,
        }
        return jsonify(result)


api.add_resource(FrequentWords, '/frequentwords/<user_id>')
api.add_resource(FileTranscription, '/transcribe')
api.add_resource(TranscriptList, '/transcripts/<string:uid>')


if __name__ == '__main__':
    app.run(debug=True)




