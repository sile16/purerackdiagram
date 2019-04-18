# purerackdiagram

This is an un-official tool to build Pure Storage rack diagrams.

## Try it out:

[Web UI](https://raw.githubusercontent.com/sile16/purerackdiagram/master/ui/index.html)

Thank you Jian Ruan for the html interface!!

## Background


Params:
model: default: "fa-x20r2", all mr2 and all x & xr2 modles are valid as of 2018Q1
face: 

This is my first lambda project.  I built this tool to explore AWS Lambda and Python 3.7 asyncio.  

I started off by basing the data-flow based on [this design pattern](https://aws.amazon.com/blogs/compute/resize-images-on-the-fly-with-amazon-s3-aws-lambda-and-amazon-api-gateway/).

At first I was tempted to just use the built in Lambda editor and just use Javascript.  However, the more I dug in, I realized I would have to build the project offline and package up dependencies where I used JS or Python.  

So, with that I decided to go back to more familiar Python territory..

First I built a caching object store, so that I could request an object from multiple places, but it would be pulled down only once and asynchronously.  That took a bit of time to do.  But worked pretty well.  It's pretty latency sensative though, even with asyncIO, i'm pulling down 8-10 images, checking if they exist and then pushing a new object out and caching it.  All in all it was taking 5-15 seconds to generate an image.

The PNG images I'm building from are small enough to be included in the code zip file directly.  This will dramatically reduce the latency of multiple pulls.  However, even though this executes in aroud < 300 ms on my local machine, it still takes several seconds in lambda.  

After including the PNG files directly into the package, it performs better.  Another bit of advice, is that if you want to increase execution time, you can increase your lambda RAM.  Even though you may not need more RAM, it will increase CPU cycles and execution will happen faster.

Also, One bit of advice, is that if you are converting to base64 to deliver a binary stream in lambda python... make sure to deliver a utf-8 encoded stream, rather than a byte stream.  I spent a couple hours tracking down why I couldn't send a binary stream. 


