package com.furax.furaxxz.launcher

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.GridLayoutManager
import com.furax.furaxxz.databinding.ActivityLauncherBinding
import com.furax.furaxxz.ui.MainActivity

/**
 * FuraxXZ's own home screen. Declared as a real Android launcher (ACTION_MAIN
 * + CATEGORY_HOME in the manifest) — selectable from the system's normal
 * "choose a launcher" picker, no root, no special permission beyond the
 * ordinary app-visibility <queries> declaration.
 */
class LauncherActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLauncherBinding
    private lateinit var repository: InstalledAppsRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLauncherBinding.inflate(layoutInflater)
        setContentView(binding.root)

        repository = InstalledAppsRepository(applicationContext)

        binding.openFuraxxzButton.setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java))
        }

        val apps = repository.listLaunchableApps()
        binding.appGrid.layoutManager = GridLayoutManager(this, GRID_COLUMNS)
        binding.appGrid.adapter = LauncherAppAdapter(apps) { app ->
            try {
                startActivity(repository.launchIntentFor(app))
            } catch (e: android.content.ActivityNotFoundException) {
                Toast.makeText(this, "Could not open ${app.label}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    companion object {
        private const val GRID_COLUMNS = 4
    }
}
