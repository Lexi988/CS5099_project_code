#app/utils/dictionary.py
import os

"""read scrabble word dict. to prevent proper nouns, abbreviations, words not in dictionary etc."""

#REF:
# Scrabble dictioanry taken from
# https://github.com/redbo/scrabble/blob/master/dictionary.txt

#

class Dictionary:
    def __init__(self, dict_file="app/data/dictionary.txt"):
        self.words = set()
        self.load_dictionary(dict_file)
        
    def load_dictionary(self, file_path):
        """Load words from dictionary file"""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    self.words.add(line.strip().upper())
        except FileNotFoundError:
            print(f"Dictionary file not found: {file_path}")
            
    def is_valid_word(self, word):
        """Check if word exists in dictionary"""
        return word.upper() in self.words
        
    def suggest_words(self, pattern, limit=10):
        """Find words matching a pattern (e.g. 'C?T')"""
        matches = []
        for word in self.words:
            if len(word) != len(pattern):
                continue
                
            match = True
            for i, char in enumerate(pattern):
                if char != '?' and char != word[i]:
                    match = False
                    break
                    
            if match:
                matches.append(word)
                if len(matches) >= limit:
                    break
                    
        return matches