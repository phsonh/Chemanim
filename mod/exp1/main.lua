local chem = require("chem")

chem.scene {
    width = 1920,
    height = 1080,
    logic_width = 960,
    logic_height = 540,
    fps = 60,
    background = "000000FF",
    title = "exp1"
}

chem.load_texture("1", "1.png", 0.5, 0.5)
chem.load_texture("2", "2.png", 0.5, 0.5)
chem.load_texture("3", "3.png", 0.5, 0.5)
chem.load_texture("4", "4.png", 0.5, 0.5)
chem.load_texture("5", "5.png", 0.5, 0.5)
chem.load_texture("6", "6.png", 0.5, 0.5)
chem.load_texture("7", "7.png", 0.5, 0.5)
chem.load_texture("8", "8.png", 0.5, 0.5)
chem.load_texture("9", "9.png", 0.5, 0.5)
chem.load_texture("10", "10.png", 0.5, 0.5)
chem.load_texture("11", "11.png", 0.5, 0.5)
chem.load_texture("12", "12.png", 0.5, 0.5)
chem.load_texture("13", "13.png", 0.5, 0.5)

local molecule1 = chem.NewMol()

molecule1.SetImage("1")

molecule1.SetPos(0, 0)

molecule1.LerpAlpha(255, 30, 0)

chem.Wait(45)

molecule1.ChangeImage("2", 72.16, 31.67, 30, 0)

chem.Wait(60)

local molecule2 = chem.NewMol()

molecule2.SetImage("3")

molecule2.SetPos(-331.2, 103.39)

molecule2.LerpPosY(-126.17, 30, 0)

molecule2.LerpAlpha(255, 30, 0)

chem.Wait(30)

local arrow1 = chem.NewArrow()

arrow1.SetColor(255, 255, 255, 255)

arrow1.SetCurve(-61.34, -68.34, -96.08, -199.4, -212.91, -148, -303.17, -127.92)

arrow1.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow2 = chem.NewArrow()

arrow2.SetColor(255, 255, 255, 255)

arrow2.SetCurve(-342.21, -150.94, -362.36, -154.47, -365.43, -163.68, -351.43, -178.59)

arrow2.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule1.ChangeImage("4", 72.44, 1.73, 30, 0)

molecule2.ChangeImage("5", -331.53, -184.14, 30, 0)

arrow1.LerpAlpha(0, 30, 0)

arrow2.LerpAlpha(0, 30, 0)

chem.Wait(60)

arrow2.Delete()

arrow1.Delete()

molecule2.LerpPosY(-318.3, 30, 0)

molecule2.LerpAlpha(0, 30, 0)

chem.Wait(30)

molecule2.Delete()

molecule1.ChangeImage("8", 148.15, -20.12, 30, 0)

chem.Wait(30)

molecule1.ChangeImage("9", 148.15, -20.12, 30, 0)

chem.Wait(30)

local arrow3 = chem.NewArrow()

arrow3.SetColor(255, 255, 255, 255)

arrow3.SetCurve(131.35, 81.81, 187.67, 93.9, 198.42, 77, 163.62, 31.11)

arrow3.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow4 = chem.NewArrow()

arrow4.SetColor(255, 255, 255, 255)

arrow4.SetCurve(193.57, -13.83, 269.61, -30.88, 229.28, -110.37, 139.42, -81.8)

arrow4.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow5 = chem.NewArrow()

arrow5.SetColor(255, 255, 255, 255)

arrow5.SetCurve(94.48, -81.81, 69.55, -53.33, 58.79, -57.94, 62.22, -95.63)

arrow5.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule1.ChangeImage("10", -56.94, -16.66, 30, 0)

arrow4.LerpAlpha(0, 30, 0)

arrow3.LerpAlpha(0, 30, 0)

arrow5.LerpAlpha(0, 30, 0)

chem.Wait(30)

arrow5.Delete()

arrow4.Delete()

arrow3.Delete()

molecule1.ChangeImage("10", -56.94, -16.66, 30, 0)

local arrow6 = chem.NewArrow()

arrow6.SetColor(255, 255, 255, 255)

arrow6.SetCurve(-89.88, -198.18, 265.82, -357.76, 143.68, -37.45, -39.18, 18.44)

arrow6.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow7 = chem.NewArrow()

arrow7.SetColor(255, 255, 255, 255)

arrow7.SetCurve(-85.26, 3.46, -91.41, -51.43, -102.94, -56.04, -119.83, -3.46)

arrow7.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow6.LerpAlpha(0, 30, 0)

arrow7.LerpAlpha(0, 30, 0)

chem.Wait(30)

arrow7.Delete()

arrow6.Delete()

molecule1.ChangeImage("11", -2.79, 4.08, 30, 0)

chem.Wait(30)

local arrow8 = chem.NewArrow()

arrow8.SetColor(255, 255, 255, 255)

arrow8.SetCurve(29.64, 3.95, 38.13, 41.77, 22.98, 46.61, -9.22, 25.03)

arrow8.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow9 = chem.NewArrow()

arrow9.SetColor(255, 255, 255, 255)

arrow9.SetCurve(-36.89, 56.66, -20.06, 70.56, -23.79, 76.26, -42.82, 86.96)

arrow9.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule1.ChangeImage("12", -97.49, 4.08, 30, 0)

arrow8.LerpAlpha(0, 30, 0)

arrow9.LerpAlpha(0, 30, 0)

chem.Wait(30)

arrow9.Delete()

arrow8.Delete()

local arrow10 = chem.NewArrow()

arrow10.SetColor(255, 255, 255, 255)

arrow10.SetCurve(-307.64, 78.35, -328.25, -103.45, -289.07, -77.72, -120.98, -44.93)

arrow10.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow11 = chem.NewArrow()

arrow11.SetColor(255, 255, 255, 255)

arrow11.SetCurve(-77.2, -48.4, -79.05, -86.43, -54.85, -88.73, -42.63, -54.15)

arrow11.LerpProgress(1, 30, 0)

chem.Wait(30)

molecule1.ChangeImage("13", -53.71, 13.3, 30, 0)

arrow10.LerpAlpha(0, 30, 0)

arrow11.LerpAlpha(0, 30, 0)

chem.Wait(30)

arrow11.Delete()

arrow10.Delete()

chem.Wait(60)
