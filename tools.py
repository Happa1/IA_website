# my_lib
import sqlite3

from flask import session
from passlib.hash import sha256_crypt

class DatabaseWorker:
    def __init__(self, name:str):
        self.name_db = name
        # Step1: Create a connection to the file
        self.connection =  sqlite3.connect(self.name_db)
        self.cursor = self.connection.cursor()

    # def run_query(self, query:str):
    #     self.cursor.execute(query) # run query
    #     self.connection.commit() # save changes

    def run_query(self, query: str, params: tuple = ()):
        self.cursor.execute(query, params)
        self.connection.commit()

    def insert(self, query:str):
        self.run_query(query)

    def search(self, query:str, multiple=False):
        results = self.cursor.execute(query)
        if multiple:
            return results.fetchall() # return multiple rows in a list
        return results.fetchone() # return single value


    def create(self):
        query="""CREATE TABLE if not exists WORDS(
                id INTEGER PRIMARY KEY,
                length INT,
                word TEXT
                )"""
        self.run_query(query)

    def close(self):
        self.connection.close()

hasher = sha256_crypt.using(rounds=30000)

def make_hash(text:str):
    return hasher.hash(text)

def check_hash(hashed_text, text):
    return hasher.verify(text, hashed_text)


def logging():
    login=False
    user_id = session.get('user_id')  # get()メソッドを使って安全に取得
    if user_id:
        login = True
    return login