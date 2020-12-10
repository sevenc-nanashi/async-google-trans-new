# async_google_trans_new
### Version 1.0.0

This is a library based on [google_trans_new](https://github.com/lushan88a/google_trans_new) but it is async!  
It's very easy to use and solve the problem that the old api which use tk value cannot be used.  
This interface is for academic use only, please do not use it for commercial use.  
  
***
  
  
Installation
====
no way :(
***
  
  
Basic Usage
=====
### Translate
```python
import asyncio
import async_google_trans_new  

 
async def coro():
    g = async_google_trans_new.google_translator()
    print(await g.translate("こんにちは、世界！","en"))
loop=asyncio.get_event_loop() 
loop.run_until_complete(coro())
-> Hello world!
```
***

=======
Advanced Usage
=====
### Translate 
### Multi Translate
```python
import asyncio
from async_google_trans_new import google_translator

 
async def coro():
    g = google_translator()
    texts = ["こんにちは、世界！", "こんばんは、世界！", "おはよう、世界！"]
    gathers = []
    for text in texts:
    	  gathers.append(g.translate(text, "en"))
    
    print(await asyncio.gather(*gathers))

loop=asyncio.get_event_loop() 
loop.run_until_complete(coro())
-> ['Hello World! ', 'Good evening, the world! ', 'Good morning, the world! '] 
```
***

Prerequisites
====
* **Python >=3.6**  
* **aiohttp**  
* **asyncio**  
***
  
License
====
async_google_trans_new is licensed under the MIT License. The terms are as follows:  

```
MIT License  

Copyright (c) 2020 sevenc-nanashi  

Permission is hereby granted, free of charge, to any person obtaining a copy  
of this software and associated documentation files (the "Software"), to deal  
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell  
copies of the Software, and to permit persons to whom the Software is  
furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all  
copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  
SOFTWARE.  
```
