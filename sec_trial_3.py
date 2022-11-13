
import time, requests, re
from nltk.corpus import stopwords, cmudict
# from nltk.tokenize import word_tokenize  #unused
import nltk
from collections import Counter
import pandas as pd
from bs4 import BeautifulSoup as bs
from folder_paths import *  #contains paths to certain files(stopwords.txt, ciklist.xlsx and such)
# used in the script





base_url=r'https://www.sec.gov/Archives/' #url of the website
#resources_path= path to resources directory as imported from module folder_paths.py
#reports_path= path to reports folder as imported from module folder_paths.py
stop_words_path=resources_path + r"stop_words_all.txt"



def set_of_remove_words():
    """ returns the set of stop words to be removed from the extracted text
    includes stopwords from nltk.corpus and 
    from stop_words_generic.txt and stop_words_datetime.txt
    from https://sraf.nd.edu/textual-analysis/resources/#StopWords """
    remove=set(stopwords.words('english')) #stop words as in nltk
    with open(file=resources_path + r"stop_words_all.txt", mode='rt') as f: 
        #file points to path to file containing both stop_words_generic.txt and stop_words_datetime.txt
        remove |= set([x.lower().strip() for x in f.readlines()]) # additional stopwords included
    return remove# set of stopwords to be removed

def nsyl(word):
    """counts and returns the no. of syllables 
    for the given word. Uses cmudict from nltk.corpus"""
    syl_count=0
    if word[-2:]=="ed" or word[-2:]=="es":# to exclude the terminal 'es' and 'ed' as mentioned in objective
        word=word[:-2]
    try:# if word is present in nltk's cmudict.dict
        for y in syllable_dict[word.lower()][0]:#cmudict has more than one pronunciation. the code uses the first one for syllable counting 
            if y[-1].isdigit():
                syl_count +=1
    except KeyError:# word is not present in cmudict
        pass
    return syl_count# calculated no of syllables

def response_parser(response, url):
    """function to parse the http response after get request.
    The website uses inconsistent file types which necessitates the use of a modified parser.
    During text extraction, txt formats and html formats were encountered. bs4 has been used to
    parse the html formats
    """
    text=response.text
    if (not text.find(r"<HTML>")==-1) and (not text.rfind(r"</HTML>")==-1)\
        or (not text.find(r"<html>")==-1) and (not text.rfind(r"</html>")==-1):# determines the file type as html
        soup=bs(response.content , "html.parser")
        text="\n".join([x.text for x in soup.select('HTML')])# one file had multiple html tags. this line overcomes that issue     
        print("returning soup")
        return text
    text=(text[text.find(r'<TEXT>'):text.rfind(r'</TEXT>')])
    return text


""" sets of words of different categories"""
positive_words=set(pd.read_excel(resources_path+"sentiment_dictionary.xlsx", 
                                sheet_name=2, header=None).
                                applymap(lambda x: x.lower())[0]) #third sheet is for positive words
negative_words=set(pd.read_excel(resources_path+"sentiment_dictionary.xlsx", 
                                sheet_name=1, header=None).
                                applymap(lambda x: x.lower())[0]) #2nd sheet is for negative words
uncertainty_words=set(pd.read_excel(resources_path+"uncertainty_dictionary.xlsx").
                                applymap(lambda x: x.lower())["Word"])
constraining_words=set(pd.read_excel(resources_path+"constraining_dictionary.xlsx").
                                applymap(lambda x: x.lower())["Word"])
remove_words=set_of_remove_words()#includes stopwords
not_words=set(['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx'])
syllable_dict=cmudict.dict()


"""input output files"""
cik_list=pd.read_excel(resources_path+"cik_list.xlsx")#input
output_data=pd.read_excel(resources_path+"output_data.xlsx") # output file


 
tokenizer=nltk.RegexpTokenizer(r'[a-zA-Z]+[-]?[a-zA-Z]+')#used for getting words from the extracted raw text

with open(file=(reports_path+"all_reports_summary.txt"), mode='wt', encoding='utf-8' ) as text_file:
    """The file was made to keep a summary of the extraction process for my own reference"""
    rows=len(cik_list.index)
    i=0 # represents index of the cik_list dataframe during iteration
    while(i<rows):
        #print("sleeping") personal use
        time.sleep(1)# to prevent ip blocking
        #row attributes from cik_list dataframe
        cik=cik_list.loc[i]["CIK"]
        coname=cik_list.loc[i]["CONAME"]
        fyrmo=cik_list.loc[i]["FYRMO"]
        fdate=cik_list.loc[i]["FDATE"]
        form=cik_list.loc[i]["FORM"]
        secfname=cik_list.loc[i]["SECFNAME"]

        response=requests.get(base_url+secfname)# proxies={'https': r'http://51.222.67.213:32768'}  
        # proxies were not necessary as the website allowed enough requests per second.
        # nevertheless, i wrote a script to extract working proxies
        time.sleep(1) #to ensure the response was loaded before proceeding to extraction   
        text= response_parser(response, base_url+secfname) #response_parser uses appropriate parsing
        #to return the required text    
        sentence_count=len(re.findall(r".+?[^?!.][?!.]\s", text)) #regex expression to match sentences
        """for my refernce, i stored the raw extracted text
        with open(file=reports_path+f"%s_{cik}_{coname.split()[0]}"%i, mode='wt', encoding='utf-8') as f:
            f.write(text)
        """
        
        text_tokens=tokenizer.tokenize(text)#returns words as list
        unique_tokens=Counter(text_tokens)#makes a frequency dictionary for each unique word
        
        
        word_frequency={}
        for key in unique_tokens.keys():#to calculate word count
            if not key in not_words:# removes string of charaters that are not words.
                #does not remove stopwords
                word=key.strip().lower()
                if word in word_frequency:
                    word_frequency[word]+=unique_tokens[key]
                else:
                    word_frequency[key.strip().lower()]=unique_tokens[key]
        word_count=sum(word_frequency.values())#no of words including stopwords

        #to remove stopwords
        word_frequency={}
        for key in unique_tokens.keys():
            if not key in remove_words:
                word_frequency[key.strip().lower()]=unique_tokens[key]
        del(unique_tokens)
        cleaned_word_count=sum(word_frequency.values()) #no of words used in sentiment analysis 
        
        if not cleaned_word_count: # to ensure cleaned words is not empty
            continue# if empty there might have been a problem in loading the response. 
                    #this repeats the process to ensure that does not happen

        """ 
        NEXT loop DOES THE FOLLOWING
        Now, iterate over each word in word frequency and check if it is:
        1. positive
        2. negative
        3. constraining
        4. uncertainty
        5. complex word (remove terminal 'es' and 'ed' before operation)
        """
        #initialise to 0
        positive_count, negative_count, constraining_count, uncertainty_count, complex_count=0,0,0,0,0

        for word, frequency in word_frequency.items():
            if word in positive_words:
                positive_count += frequency
            elif word in negative_words:
                negative_count += frequency
            elif word in constraining_words:
                constraining_count += frequency
            elif word in uncertainty_words:
                uncertainty_count += frequency
            if nsyl(word) >2:#nsyl(word) return no of syllables
                complex_count +=frequency
        
        # for early analysis and my reference. not necessary for finding output
        """
        s="ind=%s "%i + "p=%s "%positive_count+ "n=%s "%negative_count + "c=%s "%constraining_count + \
          "u=%s "%uncertainty_count + "com=%s "%complex_count + "wc=%s "%word_count + \
          "sc=%s"%sentence_count  
        text_file.write(s+"\n")
        """
        
        # ensures each variable has a non zero count as a text is bound to have them unless 
        # an error has occured 
        if (not positive_count) and (not negative_count) and (not constraining_count) and \
           (not uncertainty_count) and  (not complex_count):
           continue
        
        
        """ calculates the required fields"""   
        #Polarity Score = (Positive Score – Negative Score)/ ((Positive Score + Negative Score) + 0.000001)
        polarity_score= (positive_count-negative_count)/((positive_count+negative_count)+0.000001)
        average_sentence_length=word_count/sentence_count
        percentage_complex=complex_count/word_count
        #Fog Index = 0.4 * (Average Sentence Length + Percentage of Complex words)
        fog_index= 0.4 * (average_sentence_length+percentage_complex)
        positive_proportion=positive_count/word_count
        negative_proportion=negative_count/word_count
        uncertainty_proportion=uncertainty_count/word_count
        constraining_proportion=constraining_count/word_count
        
        """writing the calculated values in the dataframe"""
        output_data.loc[i]={'CIK': cik,
                            'CONAME': coname ,
                            'FYRMO': fyrmo ,
                            'FDATE': fdate ,
                            'FORM': form ,
                            'SECFNAME': secfname ,
                            'positive_score':positive_count,
                            'negative_score':negative_count,
                            'polarity_score':polarity_score,
                            'average_sentence_length':average_sentence_length,
                            'percentage_of_complex_words':percentage_complex,
                            'fog_index':fog_index,
                            'complex_word_count':complex_count,
                            'word_count':word_count,
                            'uncertainty_score':uncertainty_count,
                            'constraining_score':constraining_count,
                            'positive_word_proportion':positive_proportion,
                            'negative_word_proportion':negative_proportion,
                            'uncertainty_word_proportion':uncertainty_proportion,
                            'constraining_word_proportion':constraining_proportion,
                            'constraining_words_whole_report': constraining_count }
                            #I could not understand <constraining_words_whole_report>
        
        #values after each file has been analysed to see if error has crept in("inadvertently")
        print("%s, %s"%(output_data.loc[i]['average_sentence_length'], sentence_count))      
        i+=1
    output_data.to_excel('out4.xlsx')# saves to xlsx file.
