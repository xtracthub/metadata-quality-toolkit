import pandas as pd
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import re

class Summary:
    def __init__(self):
        pass

    def get_quality_scores(self, rootdir):
        self.rootdir = rootdir
        self.tfidf_df, self.max_field = self.create_tfidf_df_and_max()
        summary = {}
        for subdir, dirs, files in os.walk(rootdir):
            for filename in files:
                filepath = subdir + os.sep + filename
                stats = {}
                stats['readability'] = self.readability_score(filepath)
                stats['completeness'] = self.completeness_score(filepath)
                stats['entropy'] = self.entropy_score(filepath)              
                stats['yield'] = self.yield_score(filepath)
                summary[filepath] = stats
        return summary

    def get_fields(self, data, field_dict):
        for field in data:
            if isinstance(data[field], dict) == False:
                field_dict[field] = []
            else:
                field_dict[field] = self.get_fields(data[field], {})
        return field_dict

    def flatten_fields(self, fields, fields_list, prefix):
        p = prefix
        for field in fields:
            prefix = p
            if fields[field] == []:
                if prefix == '':
                    fields_list.append(field)
                else:
                    fields_list.append(prefix + ':' + field)
            else:
                if prefix == '':
                    prefix = field
                else:
                    prefix = prefix + ':' + field
                self.flatten_fields(fields[field], fields_list, prefix)
        return fields_list
    
    def create_tfidf_df_and_max(self):
        corpus = []
        self.rows = {}
        index = 0
        fields = []
        for subdir, dirs, files in os.walk(self.rootdir):
            for file in files:
                filepath = subdir + os.sep + file
                with open (filepath, 'r') as f:
                    data = json.load(f)
                    # tfidf
                    vals = self.flatten_values(data)
                    newlist = [val for val in vals if isinstance(val, str)]
                    text = " ".join(newlist)
                    corpus.append(text)
                    self.rows[filepath] = index
                    index += 1
                    # max_fields
                    if data != None:
                        cur_fields = self.flatten_fields(self.get_fields(data, {}), [], '')
                        for field in cur_fields:
                            if field not in fields:
                                fields.append(field)
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
        df = pd.DataFrame(vectors.toarray(), columns = feature_names)
        return (df, len(fields))

    def completeness_score(self, filepath):        
        with open(filepath, 'r') as f:
            data = json.load(f)
            cur_fields = self.get_fields(data, {})
            cur_flattened_fields = self.flatten_fields(cur_fields, [], '')
            cur_number_of_fields = len(cur_flattened_fields)
        percent = (cur_number_of_fields/self.max_field) * 100
        return percent

    def flatten_values(self, data):
        vals = []
        for key in data:
            if isinstance(data[key], dict):
                x = self.flatten_values(data[key])
                vals.extend(x)
            else:
                if isinstance(data[key], list):
                    vals.extend(data[key])
                else:
                    vals.append(data[key])
        return vals


    def entropy_score(self, filepath):
        with open (filepath, 'r') as f:
            data = json.load(f)
            vals = self.flatten_values(data)
            fields = [val for val in vals if isinstance(val, str)]
            info = 0
            for field in fields:
                words = field.split(' ')
                for word in words:
                    try:
                        word_vals = self.tfidf_df[word]
                        word_score = word_vals[self.rows[filepath]]
                    except:
                        word_score = 0
                    info += word_score
        score = info
        return score
    
    def yield_score(self, filepath):
        return os.path.getsize(filepath)

    def count_words(self, text):
        words = text.split(None)
        return len(words)


    def count_sentences(self, text):
        sentences = 0
        end_sentence = ['.', '!', '?', ':', ';']
        for mark in end_sentence:
            sentences += text.count(mark)
        return sentences

    def count_syllables(self, text):
        syllables = 0
        vowels = ['a', 'e', 'i', 'o', 'u', 'y']
        rules = ['es', 'ed']
        words = text.split(None)
        for word in words:
            word.lower()
            if len(word) <= 3:
                syllables += 1
            else:
                end = word[-2:]
                if end in rules:
                    word = word[:-2]
                elif end == 'le':
                    word = word
                elif end[1] == 'e':
                    word = word[:-1]
                for vowel in vowels:
                    syllables += word.count(vowel)
        return syllables

    def flesch(self, text):
        n = self.count_sentences(text)
        w = self.count_words(text)
        l = self.count_syllables(text)
        if n == 0:
            n = 1
        if w == 0:
            w = 1
        f = 206.835 - 1.015 * (w/n) - 84.6 * (l/w)
        return f
        
    def readability_score(self, filepath):
        count = 0
        total_flesch = 0
        with open(filepath, 'r') as f:
            data = json.load(f)
            vals = self.flatten_values(data)
            num_count = 0
            for val in vals:
                if isinstance(val, str):
                    count += 1
                    nums = re.findall("[0-9]+\.[0-9]+", val)
                    num_count += len(nums)
                    val = re.sub("[0-9]+\.[0-9]+", "", val)
                    total_flesch += self.flesch(val)
        # No strings in the metadata
        if count == 0:
            return 0
        return (total_flesch/count, num_count)
