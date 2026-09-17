package com.furax.furaxxz.ui

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.furax.furaxxz.databinding.ActivityCategoryBinding
import com.furax.furaxxz.engine.PersonalizationEngine
import com.furax.furaxxz.model.Category

class CategoryActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCategoryBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCategoryBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val categoryName = intent.getStringExtra(EXTRA_CATEGORY) ?: Category.FONTS.name
        val category = Category.valueOf(categoryName)

        val engine = PersonalizationEngine(applicationContext)
        val items = engine.catalog.listItems(category)

        binding.categoryTitle.text = category.displayName
        binding.emptyState.visibility = if (items.isEmpty()) View.VISIBLE else View.GONE

        binding.itemList.layoutManager = LinearLayoutManager(this)
        binding.itemList.adapter = CatalogItemAdapter(items)
    }

    companion object {
        const val EXTRA_CATEGORY = "extra_category"
    }
}
