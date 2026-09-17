package com.furax.furaxxz.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.furax.furaxxz.databinding.ItemCategoryBinding
import com.furax.furaxxz.model.Category

class CategoryAdapter(
    private val categories: List<Category>,
    private val counts: Map<Category, Int>,
    private val onClick: (Category) -> Unit,
) : RecyclerView.Adapter<CategoryAdapter.ViewHolder>() {

    inner class ViewHolder(val binding: ItemCategoryBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemCategoryBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val category = categories[position]
        val count = counts[category] ?: 0
        holder.binding.categoryName.text = category.displayName
        holder.binding.categoryCount.text = if (count == 1) "1 item" else "$count items"
        holder.binding.root.setOnClickListener { onClick(category) }
    }

    override fun getItemCount(): Int = categories.size
}
