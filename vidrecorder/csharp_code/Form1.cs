/******************************************************************************
 * IBCS Proprietary
 * 
 * File: Form1.cs
 * Project: Workstation_Desktop_Recorder
 * Desc: Graphical interface to record warfighter workstation desktop sessions.
 *       The video is being multicast by the RNA. This application is a 
 *       wrapper to VLC which is the tool capturing and saving the video
 *       streams. 
 * Author: Aaron Rathz
 * 
 * Rev History:
 *       09/24/2019      arathz      Created
 ******************************************************************************/

using System;
using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;
using System.Net;
using System.Threading;
using System.IO;
using Microsoft.VisualBasic;
using System.Collections.Generic;

namespace Workstation_Desktop_Recorder
{
    public partial class Form1 : Form
    {
        // Global vars
        private Image stopImg = Properties.Resources.toggleOffSmall;
        private Image startImg = Properties.Resources.toggleOnSmall;
        private Bitmap icon = Properties.Resources.recorder_icon;
        private List<DeviceRecorder> devices = new List<DeviceRecorder>();
        pleaseWaitFrm pleaseWait = new pleaseWaitFrm();

        // Constructor - Initialize record interval and create recording objects
        public Form1()
        {
            InitializeComponent();
            this.Icon = Icon.FromHandle(icon.GetHicon());
            string answer = Interaction.InputBox("Enter time in minutes:", "Video Clip Length", "1");
            int interval = 0;
            try
            {
                interval = Int32.Parse(answer);
                interval *= 60000;
                if (interval < 60000)
                {
                    interval = 60000;
                    MessageBox.Show("Setting to minimum of 1 minute\n\nTo choose a different time, restart program");
                }
                else if (interval > 7200000)
                {
                    interval = 7200000;
                    MessageBox.Show("Setting to maximum of 120 minutes\n\nTo choose a different time, restart program");
                }
            }
            catch (Exception e)
            {
                MessageBox.Show("Setting to default 120 minutes\n\nTo choose a different time, restart program");
            }
            for (int i=1; i<=10; ++i)
            {
                devices.Add(new DeviceRecorder(i, interval));
            }
        }

        // Click action handlers
        private void Ws1Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[0]);
        }
        private void Ws2Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[1]);
        }
        private void Ws3Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[2]);
        }
        private void Ws4Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[3]);
        }
        private void Ws5Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[4]);
        }
        private void Ws6Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[5]);
        }
        private void Ws7Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[6]);
        }
        private void Ws8Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[7]);
        }
        private void Ws9Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[8]);
        }
        private void Ws10Btn_Click(object sender, EventArgs e)
        {
            buttonHandler(sender as Button, devices[9]);
        }

        // Handles all button clicks to decide what to do
        private void buttonHandler(Button myButton, DeviceRecorder device)
        {
            if (device.started)
            {
                myButton.Image = stopImg;
                device.stop();
            }
            else
            {
                myButton.Image = startImg;
                pleaseWait.Show();
                pleaseWait.Update();
                if (!device.start())
                {
                    myButton.Image = stopImg;
                    string message = "Unable to retrieve the video description file. \nUnable to start recording workstation " + (device.Workstation) + "\nTry again";
                    string caption = "ERROR";
                    MessageBox.Show(message, caption, MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                pleaseWait.Hide();
            }
        }

        // Check for running devices before closing form
        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            foreach (DeviceRecorder device in devices)
            {
                if (device.started)
                {
                    e.Cancel = true;
                }
            }
            if (e.Cancel)
            {
                MessageBox.Show("You must stop all recordings before closing the application", "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        // check for running devices before closing form
        private void CloseBtn_Click(object sender, EventArgs e)
        {
            bool stillGoing = false;
            foreach (DeviceRecorder device in devices)
            {
                if (device.started)
                {
                    stillGoing = true;
                }
            }
            if (stillGoing)
            {
                MessageBox.Show("You must stop all recordings before closing the application", "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            else
            {
                Close();
            }
        }
    }

    // Class that handles the recording thread of each workstation
    class DeviceRecorder
    {
        private int workstationNum;
        private Thread thread;
        private static StreamWriter errorLogger;
        private static StreamWriter outputLogger;
        private bool restartNeeded;
        public bool started;
        private int interval;
        public DeviceRecorder(int wsNumber, int time)
        {
            workstationNum = wsNumber;
            started = false;
            errorLogger = null;
            outputLogger = null;
            restartNeeded = false;
            interval = time;
        }

        // getter for which workstation this object instance is associated
        public int Workstation
        {
            get
            {
                return this.workstationNum;
            }
        }

        // Start the thread to record and sets the started flag
        public bool start()
        {
            if (started)
            {
                return false;
            }
            else if (!getSDPFile())
            {
                return false;
            }
            started = true;
            thread = new Thread(recordLoop);
            thread.IsBackground = true;
            thread.Start();
            return true;
        }

        // Unsets the started flag
        public void stop()
        {
            started = false;
        }

        // Set up and kick off VLC. Watch for started flag to return false. Record for
        // the set interval length then repeat.
        private void recordLoop()
        {
            string drive = (workstationNum % 2 == 0) ? "F" : "E";
            string timeStamp = DateTime.Now.ToString("'D'yyyyMMdd'T'HHmmss");
            string sdpFile = Path.GetFullPath($"ws{workstationNum}.sdp");

            Process vlc = new Process();
            vlc.StartInfo.FileName = @"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe";
            vlc.StartInfo.UseShellExecute = false;
            vlc.StartInfo.RedirectStandardError = true;
            vlc.ErrorDataReceived += new DataReceivedEventHandler(vlcErrorHandler);
            vlc.StartInfo.RedirectStandardOutput = true;
            vlc.OutputDataReceived += new DataReceivedEventHandler(vlcOutputHandler);
            vlc.StartInfo.Arguments = $"-I dummy --verbose=\"1\" {sdpFile} --sout=file/ts:\"{drive}:\\ws{workstationNum}{timeStamp}.mp4\"";
            vlc.Start();
            vlc.BeginErrorReadLine();
            vlc.BeginOutputReadLine();

            FileInfo videoMonitor = new FileInfo($"{drive}:\\ws{workstationNum}{timeStamp}.mp4");
            int zeroCount = 0;
            long byteCounter = 0;
            //StreamWriter sw = new StreamWriter($@"c:\Users\Administrator\Desktop\monitor{workstationNum}.txt");

            DateTime start = DateTime.Now;
            Stopwatch timer = Stopwatch.StartNew();

            while (started)
            {
                if (timer.ElapsedMilliseconds > interval || restartNeeded || vlc.HasExited)
                {
                    if (!vlc.HasExited)
                    {
                        vlc.CancelErrorRead();
                        vlc.CancelOutputRead();
                        vlc.Kill();
                        vlc.WaitForExit();
                    }
                    timeStamp = DateTime.Now.ToString("'D'yyyyMMdd'T'HHmmss");
                    vlc.StartInfo.Arguments = $"-I dummy --verbose=\"1\" {sdpFile} --sout=file/ts:\"{drive}:\\ws{workstationNum}{timeStamp}.mp4\"";
                    vlc.Refresh();
                    vlc.Start();
                    vlc.BeginErrorReadLine();
                    vlc.BeginOutputReadLine();
                    timer.Restart();
                    restartNeeded = false;
                    zeroCount = 0;
                    byteCounter = 0;
                    videoMonitor = new FileInfo($"{drive}:\\ws{workstationNum}{timeStamp}.mp4");
                }
                videoMonitor.Refresh();
                if (videoMonitor.Exists)
                {
                    if (videoMonitor.Length > byteCounter)
                    {
                        byteCounter = videoMonitor.Length;
                        zeroCount = 0;
                    }
                    else if (++zeroCount > 20)
                    {
                        restartNeeded = true;
                    }
                }
                Thread.Sleep(500);
            }
            timer.Stop();
            vlc.Kill();
            vlc.WaitForExit();
        }

        // Handles the standard error from VLC
        private static void vlcErrorHandler(object sender, DataReceivedEventArgs vlcError)
        {
            string logLocation = "E:";
            string logName = "errorlog.txt";
            if (!String.IsNullOrEmpty(vlcError.Data))
            {
                if (errorLogger == null)
                {
                    try
                    {
                        errorLogger = new StreamWriter($"{logLocation}\\{logName}", true);
                    }
                    catch (Exception e)
                    {
                        MessageBox.Show($"Error opening errorlog file \n{e.Message.ToString()}");
                    }
                }
                if (errorLogger != null)
                {
                    errorLogger.WriteLine(vlcError.Data);
                    errorLogger.Flush();
                    // errorLogger.Close();
                }
            }
        }

        // Handles the standard output from VLC
        private static void vlcOutputHandler(object sender, DataReceivedEventArgs vlcOutput)
        {
            string logLocation = "E:";
            string logName = "outputlog.txt";
            if (!String.IsNullOrEmpty(vlcOutput.Data))
            {
                if (outputLogger == null)
                {
                    try
                    {
                        outputLogger = new StreamWriter($"{logLocation}\\{logName}", true);
                    }
                    catch (Exception e)
                    {
                        MessageBox.Show($"Error opening outputlog file \n{e.Message.ToString()}");
                    }
                }
                if (outputLogger != null)
                {
                    errorLogger.WriteLine(vlcOutput.Data);
                    errorLogger.Flush();
                    // errorLogger.Close();
                }
            }
        }

        // Retrieves the sdp file from the RNA. Address ranges from 192.168.5.71 for
        // workstation 1 to 192.168.5.80 for workstation 10.
        private bool getSDPFile()
        {
            int octet = workstationNum + 70;
            string uri = $"https://192.168.5.{octet}/dapi/media_v1/resources/encoder0/session/?command=get";
            NetworkCredential creds = new NetworkCredential("admin", "ineevoro");
            CredentialCache credCache = new CredentialCache();
            credCache.Add(new Uri(uri), "basic", creds);
            ServicePointManager.ServerCertificateValidationCallback = delegate { return true; }; // ignore cert error
            WebRequest request = WebRequest.Create(uri);
            request.Credentials = credCache;
            HttpWebResponse response = null;
            try
            {
                response = (HttpWebResponse)request.GetResponse();
            }
            catch (Exception e)
            {
                //MessageBox.Show(e.Message.ToString(), $"ERROR contacting RNA at {uri}", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
            if (!response.StatusDescription.ToLower().Equals("ok"))
            {
                MessageBox.Show("Response for sdp file NOT ok");
                response.Close();
                return false;
            }
            else
            {
                // download the sdp file from the RNA
                Stream dataStream = response.GetResponseStream();
                StreamReader reader = new StreamReader(dataStream);
                string responseFromServer = reader.ReadToEnd();
                StreamWriter outfile = new StreamWriter($"ws{workstationNum}.sdp");
                outfile.WriteLine(responseFromServer);
                // close file streams
                outfile.Close();
                reader.Close();
                dataStream.Close();
                // finally, parse the sdp file to remove any extraneous stream data
                string sdp = File.ReadAllText($"ws{workstationNum}.sdp");
                File.WriteAllText($"ws{workstationNum}.sdp", parseSDP(sdp));
            }
            response.Close();
            return true;
        }

        // The RNA can be configured to encode multiple types of streams. The only
        // stream we are concerned with is the H264 stream. It is necessary to parse
        // out the relevant lines from the sdp file so that VLC knows which stream
        // to play and record.
        private string parseSDP(string sdp)
        {
            string[] sdpArray = sdp.Split('\n');
            string finalSDP = String.Empty;

            // start with template //
            finalSDP = "v=0\r\n" +
                        "t=0 0\r\n" +
                        "a=labelp:screen0 location=0 0 3840 2400\r\n" +
                        "a=labelp:screen1 location=3840 0 3840 2400\r\n" +
                        "m=video 5004 RTP/AVP 96\r\n" +
                        "b=AS:12000\r\n" +
                        "a=rtpmap:96 H264/90000\r\n" +
                        "a=framerate:30\r\n" +
                        "a=label:screen0\r\n";

            for (int i = 0; i < sdpArray.Length; ++i)
            {
                if (sdpArray[i].StartsWith("o="))
                {
                    finalSDP += sdpArray[i] + "\r\n";
                }
                else if (sdpArray[i].StartsWith("c="))
                {
                    if (i + 1 < sdpArray.Length && sdpArray[i + 1].Contains("b=AS:12000"))
                    {
                        finalSDP += sdpArray[i] + "\r\n";
                    }
                }
                else if (sdpArray[i].Contains("ssrc="))
                {
                    finalSDP += sdpArray[i] + "\r\n";
                }
            }
            return finalSDP;
        }
    }
}
