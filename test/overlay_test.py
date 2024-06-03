import wx

class FancyFrame(wx.Frame):
    def __init__(self):
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, title='Fancy', style = style)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyDown)
        self.SetTransparent( 220 )
        self.Show(True)

    def OnKeyDown(self, event):
        """quit if user press q or Esc"""
        if event.GetKeyCode() == 27 or event.GetKeyCode() == ord('Q'): #27 is Esc
            self.Close(force=True)
        else:
            event.Skip()

app = wx.App()
f = FancyFrame()
app.MainLoop()