# PureRackDiagram

This is an unofficial tool to build Pure Storage rack diagrams.

## Try it out:

[Web UI](https://sile16.github.io/purerackdiagram/ui/)

Special thanks to Jian Ruan for the HTML interface!

### Example FA UI

![fa ui example](https://raw.githubusercontent.com/sile16/purerackdiagram/master/ui/example_fa_ui.png)

### Example FB UI

![fb ui example](https://raw.githubusercontent.com/sile16/purerackdiagram/master/ui/example_fb_ui.png)

# Introduction

By default, this tool tries to select suitable configurations, offering the option to override these for any FlashArray from m2 to the current FA, and any FlashBlade. Be aware that just because the tool can generate an image, it doesn't necessarily mean that the configuration is valid. Here are a few examples of things that aren't validated:

- PCI Slot Population Best Practice (not checked)
- Maximum capacity (not checked)
- End of Life, controllers, datapacks (not checked)
- Mezz Selection

For valid configurations, consider using [PureSizer](sizer.purestorage.com).

## Datapacks Line

You can input multiple data packs on one line, all delimited by "/", where "-" indicates a new shelf. For example, "6/11/0.02" represents a SCM Pack, 11 TB pack, and 2 blanks all in the chassis.

"11-11" represents a chassis with 11TB and 1 Shelf 11TB dp.

### Population Order

At some point, we needed to populate from the right side moving left to accommodate SCM module best practices. Therefore, in a chassis or shelf, the last datapack specified (unless it's the first one) populates from right to left. The 1st, 2nd, 3rd, 4th, etc. (unless it's the last dp) populate from left to right.

### Blanks

We've added blanks: a blank in the chassis is 10 blanks, and a blank on a shelf is 14 blanks. Additional size blanks are available, such as 0.02 for 2 blanks, or 0.12 for 12 blanks. Use blanks to add spaces between packs or as the last datapack to avoid the right-to-left population if you prefer the open spots to be at the end.

### XL Population Order

For the XL, the population order is always from slot 0 to slot 39. The right-most reverse ordering does not apply to XL chassis.

## Shelves


The shelf type is automatically determined by the media type. SAS will be a SAS shelf and NVMe will be an NVMe shelf.


## PCI Slots

Each unit should have the correct default PCI population cards.

### Add-on Cards

The tool attempts to automatically select the best slot for the card. It recognizes that a 4fc can't fit in an hh slot and fills the slots that fit. It does NOT adhere to recommended slot population. Please refer to the Ports Guide [XR4](https://support.purestorage.com/FlashArray/FlashArray_Hardware/94_FlashArray_X/01_FlashArray_X_Product_Information/FlashArray%2F%2F%2F%2FXR4_Port_Usage_and_Definitions) / [XL](https://support.purestorage.com/FlashArray/FlashArray_Hardware/FlashArray%2F%2F%2F%2F_XL/FlashArray%2F%2F%2F%2FXL_Product_Information/FlashArray%2F%2F%2F%2FXL_Port_Usage_and_Definitions)

### PCI Override

This feature overrides both default cards and anything in add-on cards. It works best for XL as the recommended slot per card is complicated.

### SAS Modules

Due to conflicting datapack sizes, a decimal point was added to all SAS datapacks.

### XL Notes

For the chassis, the datapack population order is always left to right, or rather slots 0 to 39. We recommend using PCI override and checking slot best practices.

XL Example: 183/183/0/0-183

## FlashBlade Gen1

Blades are in the format ```<Size>:<Start Blade#>-<End Blade#>,<...>```. Blade slot numbers range from 0 to 149.

For example, 1 chassis of 17TB blades, and 1 chassis of 52, would be ```17:0-14,52:15-29```.

### Lambda Notes

This is my first Lambda project. I built this tool to explore AWS Lambda and Python 3.7 asyncio.

I started by basing the data-flow on [this design pattern](https://aws.amazon.com/blogs/compute/resize-images-on-the-fly-with-amazon-s3-aws-lambda-and-amazon-api-gateway/).

First, I built a caching object store so I could request an object from multiple places, but it would be pulled down only once and asynchronously. Although this was somewhat time-consuming, it worked quite well. However, it's quite latency-sensitive; even with asyncIO, I'm pulling down 8-10 images, checking if they exist, and then pushing out a new object and caching it. It usually takes between 5-15 seconds to generate an image.

The PNG images I'm building from are small enough to be included in the code ZIP file directly, which significantly reduces the latency of multiple pulls. Even though this executes in about 300 ms on my local machine, it still takes a few seconds in Lambda.

After including the PNG files directly into the package, it performs better. To improve execution time further, you can increase your Lambda RAM. While you might not need more RAM, it will increase the CPU cycles available, resulting in faster execution.

Also, when converting to base64 to deliver a binary stream in Lambda Python, ensure you deliver a UTF-8 encoded stream, rather than a byte stream.
