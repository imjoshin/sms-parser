import config
import gspread, re, operator, os, errno, random, time
from wordcloud import WordCloud
from textblob import TextBlob
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

def main():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(config.SHEET)

    wsSent = sh.worksheet("Sent").get_all_values()
    wsRec = sh.worksheet("Received").get_all_values()
    sentHeaders = [x.lower() for x in wsSent[0]]
    recHeaders = [x.lower() for x in wsRec[0]]

    sent = [dict(zip(sentHeaders, wsSent[row])) for row in range (1, len(wsSent))]
    rec = [dict(zip(recHeaders, wsRec[row])) for row in range (1, len(wsRec))]

    conversations = getConversations(sent, rec)

    for number in conversations:
        if len(conversations[number]['sent']) + len(conversations[number]['received']) > config.MIN_TEXTS_TO_PROCESS:
            name = "'%s' (%s)" % (conversations[number]['name'], number) if conversations[number]['name'] != "" else "'%s'" % (number)
            print(name)
            processConversation(conversations[number])

def getConversations(sent, rec):
    ret = {}

    for text in sent:
        if len(text['number']) is 11 and text['number'][:1] == "1":
            text['number'] = text['number'][1:]

        if len(text['number']) is not 10:
            continue

        if text['number'] not in ret:
            ret[text['number']] = {
                'sent': [],
                'received': [],
                'name': '',
                'number': text['number'],
            }

        ret[text['number']]['sent'].append(text)
        ret[text['number']]['name'] = text['name']

    for text in rec:
        if len(text['number']) is 11 and text['number'][:1] == "1":
            text['number'] = text['number'][1:]

        if len(text['number']) is not 10:
            continue

        if text['number'] not in ret:
            ret[text['number']] = {
                'sent': [],
                'received': [],
                'name': '',
                'number': text['number'],
            }

        ret[text['number']]['received'].append(text)
        ret[text['number']]['name'] = text['name']

    return ret

def processConversation(conversation):
    dir = "%s/%s" % (config.OUTPUT_FOLDER, conversation['name'] if conversation['name'] != '' else conversation['number'])

    if config.OUTPUT_COUNT_CSV or config.OUTPUT_WORDCLOUD:
        print("\tCounting words...")
        sentWords, receivedWords, totalWords = countWords(conversation)

    if config.OUTPUT_COUNT_CSV:
        print("\tGenerating count csv...")
        writeKeyValuePairsToFile(sentWords, "%s/sent_count.csv" % (dir))
        writeKeyValuePairsToFile(receivedWords, "%s/received_count.csv" % (dir))
        writeKeyValuePairsToFile(totalWords, "%s/total_count.csv" % (dir))

    if config.OUTPUT_WORDCLOUD:
        print("\tGenerating wordclouds...")
        generateWordCloud(sentWords, "%s/sent.jpg" % (dir))
        generateWordCloud(receivedWords, "%s/received.jpg" % (dir))
        generateWordCloud(totalWords, "%s/total.jpg" % (dir))

    if config.OUTPUT_SENTIMENT_CSV:
        print("\tGenerating sentiment csv...")
        generateSentimentAnalysis(conversation, dir)

def countWords(conversation):
    allWords = {}
    for sent in conversation['sent']:
        words = sent['text'].split()
        for word in words:
            word = re.sub("[^a-zA-Z]+", "", word).lower()
            if len(word) < config.MIN_WORD_LENGTH or word in config.IGNORED_WORDS or word[:4] == "http":
                continue

            if word not in allWords:
                allWords[word] = {
                    'sent': 0,
                    'received': 0,
                    'total': 0,
                }

            allWords[word]['sent'] += 1
            allWords[word]['total'] += 1

    for rec in conversation['received']:
        words = rec['text'].split()
        for word in words:
            word = re.sub("[^a-zA-Z]+", "", word).lower()
            if len(word) < config.MIN_WORD_LENGTH or word in config.IGNORED_WORDS or word[:4] == "http":
                continue

            if word not in allWords:
                allWords[word] = {
                    'sent': 0,
                    'received': 0,
                    'total': 0,
                }

            allWords[word]['received'] += 1
            allWords[word]['total'] += 1

    sent = extractSortedKeyFromDict('sent', allWords)
    received = extractSortedKeyFromDict('received', allWords)
    total = extractSortedKeyFromDict('total', allWords)

    return sent, received, total

def generateSentimentAnalysis(conversation, dir):
    sentAnalysis = getSentimentAnalysis(conversation['sent'])
    recAnalysis = getSentimentAnalysis(conversation['received'])
    totalAnalysis = sentAnalysis.copy()

    for time in recAnalysis:
        if time in totalAnalysis:
            totalSentAnalysis = totalAnalysis[time]['polarity'] * totalAnalysis[time]['count']
            totalRecAnalysis = recAnalysis[time]['polarity'] * recAnalysis[time]['count']

            newCount = totalAnalysis[time]['count'] + recAnalysis[time]['count']
            newPolarity = (totalSentAnalysis + totalRecAnalysis) / newCount

            totalAnalysis[time]['count'] = newCount
            totalAnalysis[time]['polarity'] = newPolarity
        else:
            totalAnalysis[time] = recAnalysis[time]

    sent = [sentAnalysis[k] for k in sorted(sentAnalysis)]
    received = [recAnalysis[k] for k in sorted(recAnalysis)]
    total = [totalAnalysis[k] for k in sorted(totalAnalysis)]

    writeSentimentAnalysis(sent, "%s/sent_analysis.csv" % (dir))
    writeSentimentAnalysis(received, "%s/received_analysis.csv" % (dir))
    writeSentimentAnalysis(total, "%s/total_analysis.csv" % (dir))

def getSentimentAnalysis(sms):
    analysis = {}

    for message in sms:
        text = re.sub("[^a-zA-Z ]+", "", message['text']).lower()
        textblob = TextBlob(text)

        # November 27, 2017 at 10:57AM
        time = datetime.strptime(message['timestamp'], '%B %d, %Y at %I:%M%p')
        timeformat = "%Y-%m-%d %H:00:00" if config.SA_GRANULARITY == "hour" else "%Y-%m-%d"
        timestr = time.strftime(timeformat)
        timeint = (time.strptime(timestr, timeformat) - datetime(1970, 1, 1)).total_seconds()

        if timeint not in analysis:
            analysis[timeint] = {
                'timestamp': timestr,
                'count': 0,
                'polarity': 0
            }

        newPolarity = (analysis[timeint]['polarity'] * analysis[timeint]['count'] + textblob.sentiment.polarity) / (analysis[timeint]['count'] + 1)
        analysis[timeint]['polarity'] = newPolarity
        analysis[timeint]['count'] += 1

    return analysis

def writeSentimentAnalysis(list, file):
    if not os.path.exists(os.path.dirname(file)):
        try:
            os.makedirs(os.path.dirname(file))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with open(file, "w") as f:
        f.write("Timestamp, Polarity, Count\n")
        for entry in list:
            f.write("%s, %s, %s\n" % (entry['timestamp'], entry['polarity'], entry['count']))

def generateWordCloud(list, file):
    textList = []
    for word in list:
        textList += [word[0]] * word[1]
    random.shuffle(textList)

    wordcloud = WordCloud(
        width=config.WC_WIDTH,
        height=config.WC_HEIGHT,
        background_color=config.WC_BGCOLOR
    )
    wordcloud.generate(' '.join(textList))
    wordcloud.to_file(file)

def writeKeyValuePairsToFile(list, file):
    if not os.path.exists(os.path.dirname(file)):
        try:
            os.makedirs(os.path.dirname(file))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with open(file, "w") as f:
        f.write("Word, Count\n")
        for word in list:
            f.write("%s, %s\n" % (str(word[0]), str(word[1])))

def extractSortedKeyFromDict(key, dictionary):
    extract = {}
    for k in dictionary:
        if dictionary[k][key] > 0:
            extract[k] = dictionary[k][key]

    return sorted(extract.items(), key=lambda x:x[1], reverse=True)

if __name__ == "__main__":
	main()
