package jp.ac.hosei.cis.gps

import android.Manifest.permission.*
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager.PERMISSION_GRANTED
import android.graphics.Color
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Build
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.RequiresApi
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlin.math.sqrt
import kotlin.math.pow



class MainActivity : AppCompatActivity(),SensorEventListener {

    private lateinit var sensorManager: SensorManager
    private lateinit var square: TextView

    private fun setUpSensorStuff() {
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager

        sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)?.also {
            sensorManager.registerListener(
                this,
                it,
                SensorManager.SENSOR_DELAY_FASTEST,
                SensorManager.SENSOR_DELAY_FASTEST
            )
        }
    }
    @SuppressLint("SetTextI18n")
    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_ACCELEROMETER){
            val sides = event.values[0]
            val upDown =event.values[1]

            square.apply{
                rotationX =upDown *3f
                rotationY = sides *3f
                rotation = -sides
                translationX = sides * -10
                translationY = upDown * 10
            }
            square.text = "Accelerometer\nup/down ${upDown.toInt()}\nleft/right ${sides.toInt()}"

            val sumAcceleration = sqrt(sides.toDouble().pow(2.0) + upDown.toDouble().pow(2.0)).toFloat()
            Grobal.stopJudge = sumAcceleration
        }

    }

    override fun onAccuracyChanged(p0: Sensor?, p1: Int) {
        return
    }


    // Java で言う class 変数の宣言
    companion object {
        // logcat のためのタグ宣言
        private const val TAG = "GPSActivity"
    }

    /**
     * 単一Permission のチェック
     * @param granted 許可されているか否か
     * @param permission Permission の文字列
     */
    private fun checkGranted(granted: Boolean?, permission: String) {
        if (granted == true) {
            Log.i(TAG, "Success $permission")
        } else {
            // toast は、ポップアップメッセージのこと
            val toast = Toast.makeText(this,
                "$permission の利用が許可されませんでした", Toast.LENGTH_SHORT)
            toast.show()
        }
    }

    /**
     * Map 中の Permission チェック
     * @param granted 許可がされているか否かの Map
     * @param permission Permission の文字列で、Map のキーとなる
     */
    private fun checkGranted(granted: Map<String, Boolean>, permission: String) {
        checkGranted(granted[permission], permission)
    }

    /**
     * Permission のチェックと要求
     * @param launcher Permission の許可を確認するためのシステムのポップアップ
     * @param permission Permisssion の文字列
     */
    private fun checkAndRequestPermission(launcher: ActivityResultLauncher<String>, permission: String) {
        // Permission が既にあるかどうかを確認
        if (ContextCompat.checkSelfPermission(
                this,
                permission,
            ) != PERMISSION_GRANTED
        ) {
            // Permission 要求をする時に、説明が必要かどうかを確認
            if (ActivityCompat.shouldShowRequestPermissionRationale(
                    this,
                    permission
                )
            ) {
                // 説明ダイアログを表示した後に、Permission を要求
                AlertDialog.Builder(this)
                    .setMessage("バックグランド実行に必要です")
                    .setPositiveButton("OK") { dialog, which ->
                        launcher.launch(permission)
                    }
                    .setNegativeButton("NG") { dialog, which ->
                        // 許可されなかった
                    }
                    .show()
            } else {
                // 説明ダイアログなしに、Permission を要求
                launcher.launch(permission)
            }
        }
    }

    /**
     * 全ての Permission 許可を求める
     */
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { granted ->
        //
        checkGranted(granted, ACCESS_FINE_LOCATION)
        checkGranted(granted, ACCESS_BACKGROUND_LOCATION)
        checkGranted(granted, FOREGROUND_SERVICE)
        checkGranted(granted, WRITE_EXTERNAL_STORAGE)
        checkGranted(granted, INTERNET)
    }

    /**
     * ACCESS_FINE_LOCATION の Permission を要求
     */
    private val requestPermissionLauncherFine = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        //
        checkGranted(granted, ACCESS_FINE_LOCATION)
    }

    /**
     * ACCESS_BACKGROUND_LOCATION の Permission を要求
     * background でも、GPS を利用するために必要
     */
    private val requestPermissionLauncherBack = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        //
        checkGranted(granted, ACCESS_BACKGROUND_LOCATION)
    }

    /**
     * FOREGROUND_SERVICE の Permission を要求
     * Service を、forground activity のように継続実行するために必要
     */
    private val requestPermissionLauncherForeground = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        //
        checkGranted(granted, FOREGROUND_SERVICE)
    }

    /**
     * WRITE_EXTERNAL_STORAGE の Permission を要求
     * GPS データの記録を可能にする
     */
    private val requestPermissionLauncherExternal = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        //
        checkGranted(granted, WRITE_EXTERNAL_STORAGE)
    }

    /**
     * INTERNET の Permission を要求
     * データ通信のために必要
     */
    private val requestPermissionLauncherInternet = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        //
        checkGranted(granted, INTERNET)
    }

    /**
     * Activity 終了時に呼び出される
     */
    override fun onDestroy() {
        sensorManager.unregisterListener(this)
        super.onDestroy()
        Log.i(TAG, "onDestroy")
    }

    /**
     * Activity 生成時に呼び出される
     */
    @RequiresApi(Build.VERSION_CODES.O)

    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)

        // 基本レイアウトをロード
        setContentView(R.layout.activity_main)

        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        square = findViewById(R.id.textView)

        // Permission のチェックと要求を行う
        checkAndRequestPermission(requestPermissionLauncherFine, ACCESS_FINE_LOCATION)
        checkAndRequestPermission(requestPermissionLauncherBack, ACCESS_BACKGROUND_LOCATION)
        checkAndRequestPermission(requestPermissionLauncherForeground, FOREGROUND_SERVICE)
        checkAndRequestPermission(requestPermissionLauncherExternal, WRITE_EXTERNAL_STORAGE)
        checkAndRequestPermission(requestPermissionLauncherInternet, INTERNET)

        // 再度、Permission を確認
        if ((ActivityCompat.checkSelfPermission(
                this, ACCESS_FINE_LOCATION
            ) != PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, ACCESS_BACKGROUND_LOCATION
            ) != PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, FOREGROUND_SERVICE
            ) != PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, WRITE_EXTERNAL_STORAGE
            ) != PERMISSION_GRANTED) ||
            (ActivityCompat.checkSelfPermission(
                this, INTERNET
            ) != PERMISSION_GRANTED)
        ) {
            // Permission が不充分な時には、ボタン設定を行わない
            // ボタンが機能しない時は、Permission を確認すること
            return
        }

        // 開始ボタンの設定
        val buttonStart = findViewById<Button>(R.id.button_start)
        // Service の Intent 作成
        val i = Intent(this, GPSService::class.java)
        // ボタンの listener を設定
        buttonStart.setOnClickListener {
            // service の起動
            startService(i)
            // startForegroundService(i)

            // テキストを計測中に変更
            val textView = findViewById<TextView>(R.id.processing)
            // テキストの背景色を変更して目立つようにする
            textView.setBackgroundColor(Color.WHITE)
            textView.setTextColor(Color.MAGENTA)
            textView.text = "走行中"
        }

        val buttonStop = findViewById<Button>(R.id.button_stop)
        buttonStop.setOnClickListener {
            stopService(i)

            // テキストを停止中に変更
            val textView = findViewById<TextView>(R.id.processing)
            // テキストの背景色を変更して目立つようにする
            textView.setBackgroundColor(Color.WHITE)
            textView.setTextColor(Color.BLACK)
            textView.text = "停止中"

            setContentView(R.layout.activity_main)

            AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        }
        setUpSensorStuff()

        val sharedPref=getSharedPreferences("config.xml", Context.MODE_PRIVATE)
        Grobal.busId=sharedPref.getInt("busId",0)


        //１）Viewの取得
        val btnStart :Button =findViewById(R.id.btnStart)

        //２）ボタンを押したら次の画面へ
        btnStart.setOnClickListener {
            val intent = Intent(this, SecondActivity::class.java)
            startActivity(intent)
        }

    }
}