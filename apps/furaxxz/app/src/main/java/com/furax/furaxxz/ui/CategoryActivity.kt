package com.furax.furaxxz.ui

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.furax.furaxxz.databinding.ActivityCategoryBinding
import com.furax.furaxxz.engine.PersonalizationEngine
import com.furax.furaxxz.engine.pack.PackManifestError
import com.furax.furaxxz.engine.theme.ThemeManifestError
import com.furax.furaxxz.engine.theme.ThemeTargetViews
import com.furax.furaxxz.model.CatalogItem
import com.furax.furaxxz.model.Category

class CategoryActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCategoryBinding
    private lateinit var engine: PersonalizationEngine
    private lateinit var category: Category

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCategoryBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val categoryName = intent.getStringExtra(EXTRA_CATEGORY) ?: Category.FONTS.name
        category = Category.valueOf(categoryName)

        engine = PersonalizationEngine(applicationContext)
        val items = engine.catalog.listItems(category)

        binding.categoryTitle.text = category.displayName
        binding.emptyState.visibility = if (items.isEmpty()) View.VISIBLE else View.GONE

        binding.itemList.layoutManager = LinearLayoutManager(this)
        binding.itemList.adapter = CatalogItemAdapter(items) { item -> onItemClicked(item) }
    }

    private fun onItemClicked(item: CatalogItem) {
        when (category) {
            Category.THEMES -> confirmAndApplyTheme(item)
            Category.PACKS -> confirmAndApplyPack(item)
            else -> Toast.makeText(this, item.name, Toast.LENGTH_SHORT).show()
        }
    }

    private fun confirmAndApplyTheme(item: CatalogItem) {
        val fileName = item.fileName
        if (fileName == null) {
            Toast.makeText(this, "Theme has no manifest file", Toast.LENGTH_SHORT).show()
            return
        }
        val manifest = try {
            engine.themes.loadFromAssets(fileName)
        } catch (e: ThemeManifestError) {
            Toast.makeText(this, "Invalid theme: ${e.message}", Toast.LENGTH_LONG).show()
            return
        }

        AlertDialog.Builder(this)
            .setTitle("Apply theme '${manifest.name}'?")
            .setMessage(
                "Colors: ${manifest.colors.size} · " +
                    "Wallpaper: ${manifest.wallpaper ?: "none"} · " +
                    "Font: ${manifest.font ?: "none"}"
            )
            .setPositiveButton("Apply") { _, _ ->
                val targets = ThemeTargetViews(
                    background = binding.itemList,
                    accentTexts = listOf(binding.categoryTitle),
                )
                val result = engine.themes.apply(manifest, targets)
                val summary = buildString {
                    append("Applied: ")
                    val applied = buildList {
                        if (result.colorsApplied) add("colors")
                        if (result.wallpaperApplied) add("wallpaper")
                        if (result.fontApplied) add("font")
                    }
                    append(applied.ifEmpty { listOf("nothing") }.joinToString())
                    if (result.skipped.isNotEmpty()) {
                        append("\nSkipped: ${result.skipped.joinToString()}")
                    }
                }
                Toast.makeText(this, summary, Toast.LENGTH_LONG).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun confirmAndApplyPack(item: CatalogItem) {
        val fileName = item.fileName
        if (fileName == null) {
            Toast.makeText(this, "Pack has no manifest file", Toast.LENGTH_SHORT).show()
            return
        }
        val manifest = try {
            engine.packs.loadFromAssets(fileName)
        } catch (e: PackManifestError) {
            Toast.makeText(this, "Invalid pack: ${e.message}", Toast.LENGTH_LONG).show()
            return
        }

        AlertDialog.Builder(this)
            .setTitle("Apply pack '${manifest.name}'?")
            .setMessage("Components: ${manifest.declaredComponents().joinToString()}")
            .setPositiveButton("Apply") { _, _ ->
                val targets = ThemeTargetViews(
                    background = binding.itemList,
                    accentTexts = listOf(binding.categoryTitle),
                )
                val result = engine.packs.apply(manifest, targets)
                val summary = buildString {
                    append("Applied: ${result.appliedComponents.ifEmpty { listOf("nothing") }.joinToString()}")
                    if (result.skippedComponents.isNotEmpty()) {
                        append("\nSkipped: ${result.skippedComponents.joinToString()}")
                    }
                }
                Toast.makeText(this, summary, Toast.LENGTH_LONG).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    companion object {
        const val EXTRA_CATEGORY = "extra_category"
    }
}
