package com.furax.furaxxz.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.furax.furaxxz.databinding.ItemCatalogEntryBinding
import com.furax.furaxxz.model.CatalogItem

class CatalogItemAdapter(private val items: List<CatalogItem>) :
    RecyclerView.Adapter<CatalogItemAdapter.ViewHolder>() {

    inner class ViewHolder(val binding: ItemCatalogEntryBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemCatalogEntryBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = items[position]
        holder.binding.itemName.text = item.name
        val authorPart = item.author?.let { " · $it" } ?: ""
        holder.binding.itemStatus.text =
            (if (item.installed) "Installed" else "Not installed") + authorPart
    }

    override fun getItemCount(): Int = items.size
}
