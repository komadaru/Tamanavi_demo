package jp.ac.hosei.cis.gps

import android.Manifest
import android.R
import android.annotation.SuppressLint
import android.app.*
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.*
import android.os.Build.VERSION.SDK_INT
import android.provider.Settings
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.*
import java.io.File
import java.io.FileWriter
import java.io.PrintWriter
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.*


/**
 * Background 実行のサービスを構築
 * このサービスは、LocationListener を兼ねている
 */
class GPSService: Service(), LocationListener {
    /**
     * GPS 取得のための LocationManager
     */
    private lateinit var locationManager: LocationManager

    /**
     *  ファイル出力のための PrintWriter
     */
    private lateinit var pw: PrintWriter

    /**
     * GET プロトコルで、緯度、経度、バスID を送信
     * URL は、環境に合わせて変更すること
     */
    private val urlString = "http://10.111.138.230:5000/gps/register?time=%s&longitude=%f&latitude=%f&bus=%d&stop=%f"

    companion object {
        private const val TAG = "GPSService"
    }

    /**
     * Service 生成時に実行する
     */

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "onCreate")


        // ファイル出力用のディレクトリを取得
        val dir: File? = this.getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS)
        if(dir != null) {
            // ファイルのシーケンシャル番号
            var num = 0
            var fileName: String
            // ファイルの空き番号を検索
            while(true) {
                fileName = dir.absolutePath + "/" + "gps" + num + ".csv"

                if(File(fileName).exists()) {
                    num++
                } else {
                    break
                }
            }

            // ファイルを PrintWriter として開く
            val fw = FileWriter(fileName)
            pw = PrintWriter(fw)
        }

        // 位置計測の開始
        locationStart()
    }

    /**
     * Foreground Service の起動時に実行される
     * 現在は、Foreground Serviceにしていないので、未使用の関数
     */
    @RequiresApi(Build.VERSION_CODES.O)
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "onStartCommand")
        val requestCode = 0
        val channelId = "default"
        val context = applicationContext
        val title: String = "GPS"
        var flags = 0
        // android version により、flag を切り替える
        if (SDK_INT >= Build.VERSION_CODES.S) {
            flags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        } else {
            flags = PendingIntent.FLAG_UPDATE_CURRENT
        }
        val pendingIntent = PendingIntent.getActivity(
            context, requestCode,
            intent, flags
        )

        // ForegroundService には、起動時に、Activity に対する Notification の設定が必須
        val notificationManager =
            context.getSystemService(NOTIFICATION_SERVICE) as NotificationManager

        // Notification　Channel 設定
        val channel = NotificationChannel(
            channelId, title, NotificationManager.IMPORTANCE_DEFAULT
        )

        channel.description = "Silent Notification"
        // 通知音を消す
        channel.setSound(null, null)
        // 通知ランプを消す
        channel.enableLights(false)
        channel.lightColor = Color.BLUE
        // 通知バイブレーション無し
        channel.enableVibration(false)
        if (notificationManager != null) {
            notificationManager.createNotificationChannel(channel)
            val notification: Notification = Notification.Builder(context, channelId)
                .setContentTitle(title)
                .setSmallIcon(R.drawable.btn_star)
                .setContentText("GPS")
                .setAutoCancel(true)
                .setContentIntent(pendingIntent)
                .setWhen(System.currentTimeMillis())
                .build()

            // startForeground
            startForeground(1, notification)
        }

        // return START_NOT_STICKY
        return START_STICKY
    }

    override fun onBind(intent: Intent) : IBinder? {
        return null
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.i(TAG, "onDestroy")
        locationManager.removeUpdates(this)
        // pw.close()
    }

    /**
     * GPS 測定開始のためのメソッド
     */
    private fun locationStart() {
        Log.d(TAG, "locationStart()")

        // Permission の再確認
        if ((ActivityCompat.checkSelfPermission(
                this, Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, Manifest.permission.ACCESS_BACKGROUND_LOCATION
            ) != PackageManager.PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, Manifest.permission.FOREGROUND_SERVICE
            ) != PackageManager.PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, Manifest.permission.WRITE_EXTERNAL_STORAGE
            ) != PackageManager.PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, Manifest.permission.INTERNET
            ) != PackageManager.PERMISSION_GRANTED)
        ) {
            return
        }

        // FusedLocationService を利用するか否かの flag
        // FusedLocationService の場合、GPS 以外に、Wifi 情報などを使って位置を推定できる
        // Build Version が 30 以上だと fused を使う方が良さそう
        // val fused = Build.VERSION.SDK_INT >= 30
        // 現在は、GPS の生データを取得するように、false に設定した。
        val fused = true

        // 測定間隔(ミリ秒)
        val interval = 5000L

        if(fused) {
            // FusedLocationService 用の設定
            val request = LocationRequest.create()
            request.interval = interval
            val fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

            // FusedLocationService のための Callback クラスを宅性
            class GPSCallback() : LocationCallback() {
                override fun onLocationAvailability(p0: LocationAvailability) {
                    super.onLocationAvailability(p0)
                }

                /**
                 * Location 情報が取得できたときに呼び出される
                 */
                override fun onLocationResult(p0: LocationResult) {
                    super.onLocationResult(p0)
                    // Latitude
                    Log.i(TAG, "onLocationChanged")
                    val location = p0.lastLocation

                    processLocation(location)
               }
            }

            fusedLocationClient.requestLocationUpdates(request, GPSCallback(), Looper.getMainLooper())
        } else {
            // locationManager 用の設定
            // Instances of LocationManager class must be obtained using Context.getSystemService(Class)
            locationManager = getSystemService(LOCATION_SERVICE) as LocationManager

            // val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager

            // GPS が利用可能であるかどうかのチェック
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                Log.d(TAG, "location manager Enabled")
            } else {
                // GPS を ON にするように、利用者に要求
                val settingsIntent = Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)
                startActivity(settingsIntent)
                Log.d(TAG, "not gpsEnable, startActivity")
            }

            // locatioManager を起動。Listener は、Service 自信に実装
            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, interval,
                0.1f, this)
        }
    }

    /**
     * Location が変更になった時に呼び出される
     */
    @SuppressLint("SimpleDateFormat")
    override fun onLocationChanged(location: Location) {
        Log.i(TAG, "onLocationChanged")
        // 位置情報についての処理を行う
        processLocation(location)
    }

    /**
     * 位置情報について、ログファイルに書き出したり、通信したりするメソッド
     * @param location 位置情報
     */
    private fun processLocation(location: Location) {
        // 時刻の取得
        val cal = Calendar.getInstance()
        val format = SimpleDateFormat("yyyy/MM/dd HH:mm:ss.SSS")
        val date = format.format(cal.getTime())
        // ファイルへの出力
        // 本番では、不要かも。
        pw.printf("%s,%f,%f%n", date, location.latitude, location.longitude)
        pw.flush()

        // HTTP 接続を切り替えるフラグ
        // ローカル実験では false に設定
        // サーバとの接続実験では、true に設定
        var http = true

        if (http) {
            // http 通信は、main thread では実行できないので、
            // 新たな thread を作成
            class HttpRunnable: Runnable {
                override fun run() {
                    val bus = Grobal.busId
                    val stop = Grobal.stopJudge

                    Log.v(TAG,stop.toString())

                    // URL文字列の生成
                    val registerUrl =
                        String.format(urlString,date, location.longitude, location.latitude, bus, stop)

                    Log.v(TAG,registerUrl)

                    // URL オブジェクトの生成
                    val url = URL(registerUrl)

                    // HTTP コネクションの作成
                    val connection = url.openConnection() as HttpURLConnection
                    connection.requestMethod = "GET"
                    connection.connect()

                    // ちゃんと送信できれば、200 が戻るはず
                    var response = connection.responseCode
                    Log.i(TAG, String.format("responsecode = %d", response))
                }
            }
            // Runnable インスタンスを Thread で実行
            val assyncRunnable = HttpRunnable()
            Thread(assyncRunnable).start()
        }
    }

    override fun onProviderEnabled(provider: String) {
    }

    override fun onProviderDisabled(provider: String) {
    }
}

