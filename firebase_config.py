import pyrebase
import firebase_admin
from firebase_admin import credentials,auth
firebaseConfig = {
  "apiKey": "AIzaSyBCCVBc3388j3AI-IbVukcuMuMwV6aC4Zg",
  "authDomain": "resume-ranker-auth.firebaseapp.com",
  "projectId": "resume-ranker-auth",
  "storageBucket": "resume-ranker-auth.firebasestorage.app",
  "messagingSenderId": "742749728226",
  "appId": "1:742749728226:web:2b14afab6fd3614a8c5dbb",
  "databaseURL":"https://resume-ranker-auth-default-rtdb.firebaseio.com/"
}   
cred = credentials.Certificate("resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json")
firebase_admin.initialize_app(cred)
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
