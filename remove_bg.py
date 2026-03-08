from PIL import Image

def remove_white_bg(img_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()

    newData = []
    # Remove white background from the first logo
    for item in datas:
        # If it's pure white or close to it, make it transparent
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(out_path, "PNG")

remove_white_bg("/Users/sage/.gemini/antigravity/brain/b99d9f2a-9ca6-4fe9-a17f-9ec4882d0cad/sikh_situation_bot_logo_1772984237282.png", "client/public/logo.png")
