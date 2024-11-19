package jp.ac.hosei.cis.gps

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity


class SecondActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        setContentView(R.layout.activity_second)

        super.onCreate(savedInstanceState)
        var subbusId = 0
        val busButton1 = findViewById<Button>(R.id.radioButton1)
        busButton1.setOnClickListener {
            subbusId = 1
        }
        val busButton2 = findViewById<Button>(R.id.radioButton2)
        busButton2.setOnClickListener {
            subbusId = 2
        }
        val busButton3 = findViewById<Button>(R.id.radioButton3)
        busButton3.setOnClickListener {
            subbusId = 3
        }
        val setButton = findViewById<Button>(R.id.setbutton)
        setButton.setOnClickListener {
            Grobal.busId = subbusId
            val sharedPref=getSharedPreferences("config.xml",Context.MODE_PRIVATE)
            sharedPref.edit().putInt("busId",subbusId).apply()
            finish()
        }


    }
}