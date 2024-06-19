from openai import OpenAI

client = OpenAI()

# List to store the conversation messages
conversation_history = [
    {"role": "assistant", "content": "Sie sind ein Assistent mit folgenden Kenntnissen: Sie kennen den Wasserverbrauch des Unternehmens und können Fragen dazu beantworten. Der Wasserverbrauch im Jahr beträgt 2340 m3, der Stromverbrauch 80.000 kWh und der Gasverbrauch 10.000 m3. Im letzten Monat wurde eine Anomalie im Stromverbrauch festgestellt. Erklären Sie nur auf Nachfrage, dass dies auf sehr grosse Produktionsmengen zurückzuführen ist." + 'Maximum Stromverbrauch (Anomalie mit Wert in kWh und Datum): '},
    {"role": "assistant", "content": "Geben Sie keine Informationen weiter, die bereits bekannt sind"},
]
starting = True
def ask_gpt(request, max_electricity):
  global api_key
  global url
  global conversation_history
  global starting

  # Append the user's message to the conversation history
  conversation_history.append({"role": "user", "content": request})
  
  if starting:
    conversation_history.append({"role": "assistant", "content": "Maximum Stromverbrauch (Anomalie mit Wert in kWh und Datum): ".join(map(str, max_electricity))})
    starting = False

  completion = client.chat.completions.create(
  model="gpt-4o",
  messages= conversation_history
  )

  return completion.choices[0].message.content

# def ask_gpt(question, conversation_till_now, max_electricity):
#   # Append the user's message to the conversation history
#   conversation_history.append({"role": "user", "content": question})
    
#   completion = client.chat.completions.create(
#     model="gpt-4o",
#     messages=[
#       {"role": "system", "content": "Sie sind ein Assistent mit folgenden Kenntnissen: Sie kennen den Wasserverbrauch des Unternehmens und können Fragen dazu beantworten. Der Wasserverbrauch im Jahr beträgt 2340 m3, der Stromverbrauch 80.000 kWh und der Gasverbrauch 10.000 m3. Im letzten Monat wurde eine Anomalie im Stromverbrauch festgestellt. Erklären Sie nur auf Nachfrage, dass dies auf sehr grosse Produktionsmengen zurückzuführen ist." + 'Maximum Stromverbrauch (Anomalie mit Wert in kWh und Datum): '.join(map(str, max_electricity))},
#       {"role": "system", "content": "Geben Sie keine Informationen weiter, die bereits bekannt sind"},
#       {"role": "assistant", "content": conversation_till_now},
#       {"role": "user", "content": question},
#     ]
#   )
#   conversation_till_now += "Frage: " + question + "Antwort: " + completion.choices[0].message.content

#   return completion.choices[0].message.content, conversation_till_now

# Wie kannst du mir helfen?
# Gibt es Anomalien in den Daten?
# Wann und wie groß war diese Anomalie?
# Wie waren die jährliche Verbräuche?