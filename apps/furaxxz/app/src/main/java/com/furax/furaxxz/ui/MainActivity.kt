package com.furax.furaxxz.ui

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.furax.furaxxz.databinding.ActivityMainBinding
import com.furax.furaxxz.engine.PersonalizationEngine
import com.furax.furaxxz.model.Category

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var engine: PersonalizationEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        engine = PersonalizationEngine(applicationContext)

        val categories = Category.all()
        val counts = categories.associateWith { engine.catalog.listItems(it).size }

        binding.categoryList.layoutManager = LinearLayoutManager(this)
        binding.categoryList.adapter = CategoryAdapter(categories, counts) { category ->
            val intent = Intent(this, CategoryActivity::class.java)
            intent.putExtra(CategoryActivity.EXTRA_CATEGORY, category.name)
            startActivity(intent)
        }
    }
}
