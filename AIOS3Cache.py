from io import BytesIO
import asyncio
import botocore
import aiobotocore
from botocore.exceptions import ClientError
total_head=0
total_gets=0
total_puts=0



class AIOS3CachedBucket:
    
    def __init__(self, aios3client, bucket):
        self.cache = {}
        self.client = aios3client
        self.bucket = bucket

class AIOS3CachedObject:

    def __init__(self, key, cached_bucket):
        self.key = key
        self.object = None
        self.obj_buff = None
        self.bucket = cached_bucket.bucket
        self.cached_bucket = cached_bucket

        self.exists_lock = asyncio.Lock()
        self.io_lock = asyncio.Lock()
        self.make_lock = asyncio.Lock()

        #add pointer to primary object
        if self.key not in self.cached_bucket.cache:
            self.cached_bucket.cache[self.key] = self
            self.primary_obj = self
            self.primary = True
        else:
            self.primary_obj = cached_bucket.cache[self.key]
            self.primary = False

    
    async def exists(self):
        if not self.primary:
            return await self.primary_obj.exists()
        
        async with self.exists_lock:
            try:
                #check to see if we already know it exists
                if self.object != None:
                    return True
            
                #try to fetch object:
                global total_head
                total_head+=1
                obj = await self.cached_bucket.client.get_object(Bucket=self.bucket, 
                                                                    Key=self.key)
                self.object = obj
                return True

            except ClientError as e:
                #looks like it does NOT exist
                self.object = None
                return False


    async def get_obj_data(self):
        if not self.primary:
            return await self.primary_obj.get_obj_data()

        async with self.io_lock: 
            try:
                if self.obj_buff:
                    return self.obj_buff
                
                #This not only tests for exist, but gets the object head
                if not await self.exists():
                    raise Exception("Can not download file: {}".format(self.key))
                
                async with self.object['Body'] as stream:
                    global total_gets
                    total_gets += 1
                    self.obj_buff = BytesIO(await stream.read())
                
                return self.obj_buff

            except ClientError as e:
                if e.response['Error']['Code'] == "NoSuchKey":
                    #We don't have the img in s3 already
                    self.object = None
                    self.obj_buff = None
                else:
                    # Something else has gone wrong.
                    raise
        
    async def put_obj_data(self, buffer):
        #still need to push to primary, as this also sets the local cache obj
        if not self.primary:
            return await self.primary_obj.put_obj_data(buffer)
        
        async with self.io_lock:
            try:
                self.obj_buff = buffer
                buffer.seek(0)
                # Uploading the image for caching
                global total_puts
                total_puts += 1
                resp = await self.cached_bucket.client.put_object(Bucket=self.bucket,
                                                    Key=self.key,
                                                    Body=buffer)
                if resp == None:
                    pass
                
                

            except ClientError as e:
                # Something else has gone wrong.
                raise