local chem = require("chem")

chem.scene {
    width = 1920,
    height = 1080,
    logic_width = 960,
    logic_height = 540,
    fps = 60,
    background = "000000FF",
    title = "a001"
}

chem.load_texture("t1", "t1.png", 1, 0)

chem.load_texture("t2", "t2.png", 1, 0)

chem.load_texture("1", "1.png", 0, 0)

chem.load_texture("2", "2.png", 0, 0)

chem.load_texture("3", "3.png", 0, 0)

chem.load_texture("4", "4.png", 0, 0)

chem.load_texture("5", "5.png", 0, 0)

chem.load_texture("6", "6.png", 0.5, 0.5)

chem.load_texture("7", "7.png", 0.5, 0.5)

chem.load_texture("8", "8.png", 0.5, 0.5)

local molecule4 = chem.NewMol()

molecule4.SetImage("t1")

molecule4.SetPos(480, -270)

molecule4.LerpAlpha(255, 30, 0)

local molecule1 = chem.NewMol()

molecule1.SetImage("1")

molecule1.SetPos(-208, -109)

molecule1.LerpAlpha(255, 30, 0)

chem.Wait(60)

molecule4.LerpAlpha(0, 30, 0)

local molecule2 = chem.NewMol()

molecule2.SetImage("7")

molecule2.SetPos(360, -148.848)

molecule2.LerpAlpha(255, 30, 0)

molecule2.LerpPosX(246.528, 15, 0)

chem.Wait(30)

molecule4.Delete()

local arrow1 = chem.NewArrow()

arrow1.SetColor(255, 255, 255, 255)

arrow1.SetCurve(190.752, -130.515, 129.243, -150.572, 65.659, -103.72, 72.509, 0)

arrow1.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow2 = chem.NewArrow()

arrow2.SetCurve(55.776, 43.505, 37.057, 56.689, 36.313, 70.818, 53.544, 85.894)

arrow2.SetColor(255, 255, 255, 255)

arrow2.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule2.LerpPos(74.405, -29.505, 30, 0)

molecule2.LerpAlpha(0, 30, 0)

arrow1.LerpAlpha(0, 30, 0)

arrow2.LerpAlpha(0, 30, 0)

chem.Wait(15)

molecule1.ChangeImage("2", 30, 0)

chem.Wait(30)

molecule2.Delete()

arrow2.Delete()

arrow1.Delete()

local arrow3 = chem.NewArrow()

arrow3.SetCurve(52.548, 80.552, 20.3, 61.781, 13.692, 46.048, 58.526, 39.017)

arrow3.SetColor(255, 255, 255, 255)

arrow3.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow4 = chem.NewArrow()

arrow4.SetColor(255, 255, 255, 255)

arrow4.SetCurve(93.007, 18.161, 108.074, 33.898, 120.181, 31.88, 129.329, 12.107)

arrow4.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow4.LerpAlpha(0, 30, 0)

arrow3.LerpAlpha(0, 30, 0)

molecule1.ChangeImage("3", 30, 0)

chem.Wait(30)

arrow4.Delete()

arrow3.Delete()

local molecule3 = chem.NewMol()

molecule3.SetImage("7")

molecule3.SetPos(408.373, -227.772)

molecule3.LerpPosY(-85.288, 30, 0)

molecule3.LerpAlpha(255, 30, 0)

chem.Wait(30)

local arrow5 = chem.NewArrow()

arrow5.SetColor(255, 255, 255, 255)

arrow5.SetCurve(361.521, -71.286, 277.174, -111.13, 233.894, -53.846, 189.671, 1.273)

arrow5.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow6 = chem.NewArrow()

arrow6.SetColor(255, 255, 255, 255)

arrow6.SetCurve(146.208, 16.286, 137.097, 34.707, 124.289, 33.853, 120.955, 12.992)

arrow6.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule1.ChangeImage("4", 30, 0)

arrow5.LerpAlpha(0, 30, 0)

arrow6.LerpAlpha(0, 30, 0)

molecule3.LerpAlpha(0, 30, 0)

chem.Wait(30)

molecule3.Delete()

local molecule5 = chem.NewMol()

molecule5.SetImage("t2")

molecule5.SetPos(480, -270)

molecule5.LerpAlpha(255, 30, 0)

local molecule6 = chem.NewMol()

molecule6.SetImage("8")

molecule6.SetPos(348.969, 78.423)

molecule6.SetScale(2, 2)

molecule6.LerpScale(1, 1, 30, 0)

molecule6.LerpAlpha(255, 30, 0)

chem.Wait(30)

local arrow7 = chem.NewArrow()

arrow7.SetColor(255, 255, 255, 255)

arrow7.SetCurve(164.036, 43.617, 187.055, 100.614, 250.112, 91.797, 308.764, 73.886)

arrow7.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule5.LerpAlpha(0, 30, 0)

arrow7.LerpAlpha(0, 30, 0)

molecule6.LerpAlpha(0, 30, 0)

molecule1.ChangeImage("5", 30, 0)

chem.Wait(60)

molecule5.Delete()
