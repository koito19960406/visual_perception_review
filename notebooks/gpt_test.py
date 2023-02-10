from chatgpt_wrapper import ChatGPT
import time

bot = ChatGPT()
text = "The continuous growth of population and urbanization increases the distribution and intensity of public space lighting (Gaston et al., 2013). Nighttime light (NTL) affects people's life and work, making life more convenient (Li et al., 2020a; Xu et al., 2022) and contributing to pedestrians’ feeling safe and comfort while walking at night (Portnov et al., 2020; Suk & Walter, 2019; Svechkina et al., 2020). Yet, light pollution associated with NTL often has negative externalities for the environment and human health (Cinzano & Falchi, 2014; Cinzano et al., 2001; Liu et al., 2020, 2022; Sun et al., 2020; Xu & Gao, 2017)."
prompt = "summarize this without citations using about 1/3 of the words: " + text
print(prompt)
start = time.time()
response = bot.ask(prompt)
print(response)  # prints the response from chatGPT
end = time.time()
print("Time taken:", end - start, "seconds")