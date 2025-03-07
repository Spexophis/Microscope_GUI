from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
import tifffile as tf
import time
sdk = atmcd(r'C:\Program Files\Andor SDK')
codes = atmcd_codes
ret = sdk.Initialize(r'C:/Program Files/Andor SDK/atmcd64d.dll')
print("Function Initialize returned {}".format(ret))

if atmcd_errors.Error_Codes.DRV_SUCCESS == ret:

    (ret, iSerialNumber) = sdk.GetCameraSerialNumber()
    print("Function GetCameraSerialNumber returned {} Serial No: {}".format(
        ret, iSerialNumber))

    # Configure the acquisition
    ret = sdk.CoolerON()
    print("Function CoolerON returned {}".format(ret))

    ret = sdk.SetTemperature(-60)
    print("Function SetTemperature returned {} target temperature -60".format(ret))

    ret = sdk.SetFrameTransferMode(0)
    print("Function SetFrameTransferMode returned {}".format(ret))

    ret = sdk.SetVSAmplitude(2)
    print("Function SetVSAmplitude returned {}".format(ret))
    ret = sdk.SetHSSpeed(0, 0)
    print("Function SetHSSpeed returned {}".format(ret))
    ret = sdk.SetVSSpeed(0)
    print("Function SetVSSpeed returned {}".format(ret))

    ret = sdk.SetAcquisitionMode(codes.Acquisition_Mode.SINGLE_SCAN)
    print("Function SetAcquisitionMode returned {} mode = Single Scan".format(ret))

    ret = sdk.SetReadMode(codes.Read_Mode.IMAGE)
    print("Function SetReadMode returned {} mode = Image".format(ret))

    ret = sdk.SetTriggerMode(codes.Trigger_Mode.INTERNAL)
    print("Function SetTriggerMode returned {} mode = Internal".format(ret))

    (ret, xpixels, ypixels) = sdk.GetDetector()
    print("Function GetDetector returned {} xpixels = {} ypixels = {}".format(
        ret, xpixels, ypixels))

    h_start, v_start = 1, 512-32
    x_end, y_end = 1024, 512+32
    xpixels = x_end - h_start + 1
    ypixels = y_end - v_start + 1
    img_size = xpixels * ypixels

    ret = sdk.SetImage(1, 1, h_start, x_end, v_start, y_end)
    print("Function SetImage returned {} hbin = 1 vbin = 1 hstart = 1 hend = {} vstart = 1 vend = {}".format(
        ret, xpixels, ypixels))

    # ret = sdk.SetImage(1, 1, 1, xpixels, 1, ypixels)
    # print("Function SetImage returned {} hbin = 1 vbin = 1 hstart = 1 hend = {} vstart = 1 vend = {}".format(
    #     ret, xpixels, ypixels))

    ret = sdk.SetEMCCDGain(240)
    print("Function SetEMCCDGain returned {}".format(ret))

    ret = sdk.SetExposureTime(0.04)
    print("Function SetExposureTime returned {} time = 0.01s".format(ret))

    (ret, fminExposure, fAccumulate, fKinetic) = sdk.GetAcquisitionTimings()
    print("Function GetAcquisitionTimings returned {} exposure = {} accumulate = {} kinetic = {}".format(
        ret, fminExposure, fAccumulate, fKinetic))

    ret = sdk.PrepareAcquisition()
    print("Function PrepareAcquisition returned {}".format(ret))

    # Perform Acquisition
    ret = sdk.StartAcquisition()
    print("Function StartAcquisition returned {}".format(ret))

    ret = sdk.WaitForAcquisition()
    print("Function WaitForAcquisition returned {}".format(ret))

    t = time.strftime("%Y%m%d%H%M%S")
    # fd = r"C:\\Users\ruizhe.lin\\Documents\\data\\20250306\\test_sif\\" + t + ".sif"
    # ret = sdk.SaveAsSif(fd)

    imageSize = xpixels * ypixels
    (ret, arr, validfirst, validlast) = sdk.GetImages16(1, 1, imageSize)
    print("Function GetImages16 returned {} first pixel = {} size = {}".format(
        ret, arr[0], imageSize))
    fd = r"C:\\Users\ruizhe.lin\\Documents\\data\\20250306\\test_tiff\\" + t + ".tiff"
    tf.imwrite(fd, arr.reshape(ypixels, xpixels))

    # Clean up
    (ret) = sdk.ShutDown()
    print("Function Shutdown returned {}".format(ret))

else:
    print("Cannot continue, could not initialise camera")
