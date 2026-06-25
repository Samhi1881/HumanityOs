import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  ...props
}) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={clsx(
        'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed',
        {
          // Variants
          'bg-brand-600 hover:bg-brand-500 text-white shadow-md shadow-brand-500/10': variant === 'primary',
          'bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700': variant === 'secondary',
          'bg-red-600/90 hover:bg-red-500 text-white shadow-md shadow-red-500/10': variant === 'danger',
          'hover:bg-slate-800 text-slate-400 hover:text-slate-100': variant === 'ghost',
          
          // Sizes
          'px-3 py-1.5 text-xs': size === 'sm',
          'px-4 py-2 text-sm': size === 'md',
          'px-5 py-2.5 text-base': size === 'lg',
        },
        className
      )}
      {...(props as any)}
    >
      {children}
    </motion.button>
  );
};
