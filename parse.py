import config
import gspread, re
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

    conversations = separate(sent, rec)

    for number in conversations:
        print("Processing conversation for '%s'" % (number))
        processConversation(conversations[number])

def separate(sent, rec):
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
            }

        ret[text['number']]['sent'].append(text)

    for text in rec:
        if len(text['number']) is 11 and text['number'][:1] == "1":
            text['number'] = text['number'][1:]

        if len(text['number']) is not 10:
            continue

        if text['number'] not in ret:
            ret[text['number']] = {
                'sent': [],
                'received': [],
            }

        ret[text['number']]['received'].append(text)

    return ret

def processConversation(conversation):
    sentWords = {}
    for sent in conversation['sent']:
        words = sent['text'].split()
        for word in words:
            word = re.sub("[^a-zA-Z]+", "", word).lower()
            if len(word) is 0 or word in config.COMMON_WORDS[20:]:
                continue

            if word not in sentWords:
                sentWords[word] = 0

            sentWords[word] += 1

    count = 0
    for key, value in sorted(sentWords.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        if count > 10:
            break
        print "%s: %s" % (key, value)
        count += 1

if __name__ == "__main__":
	main()
