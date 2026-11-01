package com.furax.furaxxz.launcher

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.furax.furaxxz.databinding.ItemLauncherAppBinding

class LauncherAppAdapter(
    private val apps: List<LauncherApp>,
    private val onClick: (LauncherApp) -> Unit,
) : RecyclerView.Adapter<LauncherAppAdapter.ViewHolder>() {

    inner class ViewHolder(val binding: ItemLauncherAppBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemLauncherAppBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val app = apps[position]
        holder.binding.appIcon.setImageDrawable(app.icon)
        holder.binding.appLabel.text = app.label
        holder.binding.root.setOnClickListener { onClick(app) }
    }

    override fun getItemCount(): Int = apps.size
}
