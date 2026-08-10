# rsys-toolbox

This package is intended for people running RailSys who are also Python enthusiasts.

It allows you to carry out analysis of your multi-sims on your laptop, within a Jupyter notebook or in Python.

The core principles:

- No UI: I believe that if you are doing any sort of analysis, there is no one solution that fits all, simply because different analyses face different problems that require different solutions. Think of this more as a toolbox than as a black box.
- Engagement: You are encouraged to participate in the development, especially if you have problems that you are not able to solve with your current tools!
- Speed: This uses Polars, no Pandas (that I have come to hate). Polars is written in Rust to do its heavy lifting, that makes everything very fast. If you really want to use Pandas, you can translate the Polars dataframe to Pandas (and yes, you can save to good'ol CSV with Polars).

For now, all you need is the extract from "Eval Manager".

Here are the functionalities currently supported:

- Exploratory analysis of your data, things like:
    - How many trains there are
    - What stations there are
    - ...
- Maybe more interestingly, there is a causality investigation tool, the idea is:
    - I have a train 1 that is late at station A
    - I believe train 2 is the one that causes the delay at station A
    - I look in the past of station A and try to find if the delays of trains 1 are correlated with the delay of trains 2 across multi-sims.
- That's all for now.