# **ZeroMatcher: A Cost-Off Entity Matching System**

Entity Matching (EM) aims to find data instances from different sources that refer to the same real-world entity. The existing EM techniques can be either costly or tailored for a specific data type. We present ZeroMatcher, a cost-off entity matching system, which supports (i) handling EM tasks with different data types, including relational tables and knowledge graphs; (ii) keeping its EM performance always competitive by enabling the sub-modules to be updated in a lightweight manner, thus reducing development costs; and (iii) performing EM without human annotations to further slash the labor costs. First, ZeroMatcher automatically suggests users a set of appropriate modules for EM according to the data types of the input datasets. Users could specify the modules for the subsequent EM process according to their preferences. Alternatively, users are able to customize the modules of ZeroMatcher. Then, the system proceeds to the EM task, where users can track the entire EM process and monitor the memory usage changes in real-time. When the EM process is completed, ZeroMatcher visualizes the EM results from different aspects to ease the understanding for users. Finally, ZeroMatcher provides EM results evaluation, enabling users to compare the effectiveness among different parameter settings.

![framework](system_overview.jpg)

## Video
Please download the file named ![video]"ZeroMatcher.mp4"
