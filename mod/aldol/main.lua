local chem = require("chem")

chem.scene {
    width = 1920,
    height = 1080,
    logic_width = 960,
    logic_height = 540,
    fps = 60,
    background = "FFFFFFFF",
    title = "aldol"
}

chem.load_texture("h20", "h20.png", 0.5, 0.5)

chem.load_texture("oh-", "oh-.png", 0.5, 0.5)

chem.load_texture("phcho", "phcho.png", 0, 0)

chem.load_texture("phcoch=chph", "phcoch=chph.png", 0, 0)

chem.load_texture("phcoch2-", "phcoch2-.png", 0, 0)

chem.load_texture("phcoch2chohph", "phcoch2chohph.png", 0, 0)

chem.load_texture("phcoch2cho-ph", "phcoch2cho-ph.png", 0, 0)

chem.load_texture("phcome", "phcome.png", 0, 0)

chem.load_texture("phcome_th", "phcome_th.png", 0, 0)

local phcome = chem.NewMol()

phcome.SetPos(-300, -150)

phcome.SetImage("phcome")

phcome.SetAlpha(0)

phcome.LerpAlpha(255, 30, 0)

chem.Wait(30)

phcome.ChangeImage("phcome_th", 30, 0)

chem.Wait(30)

local oh_ = chem.NewMol()

oh_.SetPos(300, 200)

oh_.SetImage("oh-")

oh_.SetAlpha(0)

oh_.LerpAlpha(255, 30, 0)

oh_.LerpPosX(180, 30, 0)

chem.Wait(60)

local arrow = chem.NewArrow()

local arrow2 = chem.NewArrow()

arrow.SetCurve(123.99, 219.094, -58.241, 212.532, -126.572, 77.962, -46.572, -2.038)

arrow.SetWidth(3)

arrow.SetProgress(0)

arrow2.SetCurve(-68.212, -27.497, -63.316, 18.133, -121.479, 4.13, -83.487, -44.046)

arrow2.SetWidth(3)

arrow2.SetProgress(0)

arrow.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow2.LerpProgress(1, 30, 0)

chem.Wait(30)

oh_.ChangeImage("h20", 30, 0)

phcome.ChangeImage("phcoch2-", 30, 0)

arrow.LerpAlpha(0, 30, 0)

arrow2.LerpAlpha(0, 30, 0)

chem.Wait(60)

oh_.LerpScaleX(3, 15, 0)

oh_.LerpScaleY(0, 15, 0)

chem.Wait(30)

oh_.Delete()

arrow2.Delete()

arrow.Delete()

local phcho = chem.NewMol()

phcho.SetImage("phcho")

phcho.SetScaleX(-1)

phcho.SetPos(360, -81.47)

phcho.SetAlpha(0)

phcho.LerpAlpha(255, 60, 0)

phcho.LerpPosX(315, 30, 0)

chem.Wait(60)

local arrow3 = chem.NewArrow()

local arrow4 = chem.NewArrow()

arrow4.SetProgress(0)

arrow3.SetProgress(0)

arrow3.SetCurve(-35.079, -68.74, 103.661, -159.684, 55.459, -4.383, 139.462, 40.735)

arrow4.SetCurve(136.249, 67.75, 92.691, 43.363, 52.197, 99.366, 125.67, 109.008)

arrow3.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow4.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow3.LerpAlpha(0, 30, 0)

arrow4.LerpAlpha(0, 30, 0)

chem.Wait(30)

arrow3.Delete()

arrow4.Delete()

phcome.LerpPos(-120.679, -81.562, 15, 0)

chem.Wait(5)

local object = chem.NewMol()

object.SetImage("phcoch2cho-ph")

object.SetPos(-120.465, -81.605)

object.SetAlpha(0)

object.LerpAlpha(255, 30, 0)

phcome.LerpAlpha(0, 30, 0)

phcho.LerpAlpha(0, 30, 0)

chem.Wait(30)

phcho.Delete()

phcome.Delete()

local h2o = chem.NewMol()

h2o.SetImage("h20")

h2o.SetPos(309.474, 188.211)

h2o.SetAlpha(0)

h2o.LerpAlpha(255, 30, 0)

chem.Wait(30)

local arrow = chem.NewArrow()

arrow.SetCurve(166.526, 165.474, 115.263, 221.263, 192.947, 233.895, 246.527, 202.105)

arrow.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow.LerpAlpha(0, 30, 0)

chem.Wait(30)

arrow.Delete()

object.ChangeImage("phcoch2chohph", 30, 0)

h2o.ChangeImage("oh-", 30, 0)

chem.Wait(30)

h2o.LerpPosY(305.684, 30, 0)

h2o.LerpAlpha(0, 30, 0)

chem.Wait(30)

h2o.Delete()

local arrow = chem.NewArrow()

arrow.SetCurve(108.421, -5.053, 136.498, -25.667, 150.543, -2.143, 130.356, 27.075)

arrow.LerpProgress(1, 30, 0)

chem.Wait(30)

local arrow2 = chem.NewArrow()

arrow2.SetCurve(135.332, 66.635, 62.783, 73.008, 85.67, 114.339, 127.835, 107.123)

arrow2.LerpProgress(1, 30, 0)

chem.Wait(30)

arrow.LerpAlpha(0, 30, 0)

arrow2.LerpAlpha(0, 30, 0)

object.ChangeImage("phcoch=chph", 60, 0)

chem.Wait(30)

chem.Wait(120)
