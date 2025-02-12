import json
from google.cloud import firestore
from flask import Flask, jsonify


app = Flask(__name__)

def get_firestore_client() -> firestore.Client:
   
   try:
       return firestore.Client(project="capstone-henry", database="capstone-test")
   

   except Exception as e:
       print(f"Firestore initialization failed: {e}")
       exit()
    

@app.route('/add')
def add_data():
    db = get_firestore_client()
    data = {
        "id": "3",
        "name": "Solomon",
        "age": 25
    }
    doc_ref = db.collection('users').document(data['id'])
    doc_ref.set(data)

    return jsonify({"message": "User added"})


if __name__ == "__main__":
    app.run(port=5000)