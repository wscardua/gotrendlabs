package br.com.gotrendlabs.gotrendlabs_mobile

import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return
        }
        val channel = NotificationChannel(
            "gtl_default",
            "GoTrendLabs",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Alertas de mercados, carteira e badges da GoTrendLabs"
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }
}
