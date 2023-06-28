# purerackdiagram

This is an un-official tool to build Pure Storage rack diagrams.

## Try it out:

[Web UI](https://sile16.github.io/purerackdiagram/ui/)

Thank you Jian Ruan for the html interface!!

### Example FA UI

![fa ui example](https://raw.githubusercontent.com/sile16/purerackdiagram/master/ui/example_fa_ui.png)

### Example FB UI

![fb ui example](https://raw.githubusercontent.com/sile16/purerackdiagram/master/ui/example_fb_ui.png)

# Intro
Overall the tool tries to pick good defaults, with ways to ovveride to generate
any FlashArray m2 -> FA current, and any FlashBlade.  Be cautioned that just because it can be generate an image doesn't mean it's a valid config.  Just some example of things NOT Validated:

- PCI Slot Population Best Practice (not checked)
- Capacity maximum (not checked)
- End of Life, controllers, datapacks (not checked)
- Mezz Selection

Use [pure sizer](sizer.purestorage.com) to find valid configs.  

## Datapacks line

You can put multiple data packs in one line all delimited by / , if you put a - that indicates a new shelf.
Example : 6/11/0.02    would be a SCM Pack, 11 TB pack and 2 blanks all in the chassis.

Example : 11-11    would be chassis with 11TB and 1 Shelf 11TB dp

### Population order
At some point we needed to populate from the right side going left to handle SCM modules best practice.  So in a chassis or shelf, the last datapack specified (if not the first one) will populate from right->left.  The 1st, 2nd, 3rd, 4th, ... (if not the last dp), will populate left->right.

### Blanks
We have added blanks, on the chassis a blank is 10 blanks. On a shelf a blank is 14 blanks.  We have added addition size blanks
by adding 0.02 is 2 blanks, 0.12 , is 12 blanks,  You can use blanks to add spaces between packs.   You can also use blanks as the last datapack to avoid seeing the right->left population if you want the open spots to be at the end.

### XL Population order
With XL the population order is always slot 0-> slot 39.  The right most reverse ordering doesn't apply to XL chassis.


## Shelfs
The shelf type is automatically determined by the media type.  SAS will be a SAS shelf and NVMe - NVMe shelf.

## PCI Slots
Every unit should have the correct default PCI population cards.  

### Addon Cards
Will try and auto pick the best slot for the card.  It knows a 4fc can't fit in hh slot. 
But otherwise just fills the slots that fit.  It does NOT try to follow recommended slot
population.  Please refer to the Ports Guide [xr4](https://support.purestorage.com/FlashArray/FlashArray_Hardware/94_FlashArray_X/01_FlashArray_X_Product_Information/FlashArray%2F%2F%2F%2FXR4_Port_Usage_and_Definitions) / [XL](https://support.purestorage.com/FlashArray/FlashArray_Hardware/FlashArray%2F%2F%2F%2F_XL/FlashArray%2F%2F%2F%2FXL_Product_Information/FlashArray%2F%2F%2F%2FXL_Port_Usage_and_Definitions)

### PCI Override
This will override both default cards as well as anything in addon cards.  This is the best 
for XL, as the recommended slot per card is complicated. 



### SAS Modules
Because of conflicting datapacks sizes, a decemil point was added to all SAS datapacks.



### XL Notes
For the chassis the datapack population order is alwayws left->right, or rather slots 0->39
Recommend to use PCI ovverride, and check slot best practices

XL Example: 183/183/0/0-183


## FlashBlade Gen1
Blades in format ```<Size>:<Start Blade#>-<End Blade#>,<...>``` 
blade slot #s are 0-149. 

Example,1 Chassis of 17TB blades, and 1 chassis  52, would be 
```17:0-14,52:15-29```


#### Lambda Notes

This is my first lambda project.  I built this tool to explore AWS Lambda and Python 3.7 asyncio.

I started off by basing the data-flow based on [this design pattern](https://aws.amazon.com/blogs/compute/resize-images-on-the-fly-with-amazon-s3-aws-lambda-and-amazon-api-gateway/).


First I built a caching object store, so that I could request an object from multiple places, but it would be pulled down only once and asynchronously.  That took a bit of time to do.  But worked pretty well.  It's pretty latency sensative though, even with asyncIO, i'm pulling down 8-10 images, checking if they exist and then pushing a new object out and caching it.  All in all it was taking 5-15 seconds to generate an image.

The PNG images I'm building from are small enough to be included in the code zip file directly.  This will dramatically reduce the latency of multiple pulls.  However, even though this executes in aroud < 300 ms on my local machine, it still takes several seconds in lambda.  

After including the PNG files directly into the package, it performs better.  If you want to improve execution time, you can increase your lambda RAM.  Even though you may not need more RAM, it will increase CPU cycles available and execution will happen faster.

Also, if you are converting to base64 to deliver a binary stream in lambda python... make sure to deliver a utf-8 encoded stream, rather than a byte stream.  




