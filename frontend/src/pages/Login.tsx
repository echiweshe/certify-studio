import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Mail, Lock, ArrowRight, Sparkles } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/utils'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const navigate = useNavigate()
  const { login, isLoading } = useAuthStore()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = async (data: LoginForm) => {
    setIsSubmitting(true)
    try {
      await login(data.email, data.password)
      toast.success('Welcome to Certify Studio!')
      navigate('/')
    } catch (error) {
      console.error('Login error:', error)
      toast.error('Invalid credentials. Try demo mode!')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDemoMode = async () => {
    setIsSubmitting(true)
    try {
      // Set demo credentials and submit
      setValue('email', 'demo@certifystudio.ai')
      setValue('password', 'demo123')
      
      // Direct login with demo credentials
      await login('demo@certifystudio.ai', 'demo123')
      toast.success('Welcome to Certify Studio Demo!')
      navigate('/')
    } catch (error) {
      console.error('Demo login error:', error)
      toast.error('Demo mode temporarily unavailable')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left side - Login form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10 dark:from-blue-500/5 dark:via-purple-500/5 dark:to-pink-500/5" />
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md relative z-10"
        >
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
              <Brain className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold gradient-text">Certify Studio</h1>
            <p className="text-muted-foreground mt-2">
              AI Agent Operating System for Educational Excellence
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <input
                  {...register('email')}
                  type="email"
                  className={cn(
                    "w-full pl-10 pr-4 py-2 rounded-lg",
                    "bg-card border border-input",
                    "focus:outline-none focus:ring-2 focus:ring-primary",
                    errors.email && "border-destructive"
                  )}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </div>
              {errors.email && (
                <p className="text-sm text-destructive mt-1">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <input
                  {...register('password')}
                  type="password"
                  className={cn(
                    "w-full pl-10 pr-4 py-2 rounded-lg",
                    "bg-card border border-input",
                    "focus:outline-none focus:ring-2 focus:ring-primary",
                    errors.password && "border-destructive"
                  )}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>
              {errors.password && (
                <p className="text-sm text-destructive mt-1">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className={cn(
                "w-full flex items-center justify-center space-x-2",
                "px-4 py-2 rounded-lg font-medium",
                "bg-primary text-primary-foreground",
                "hover:bg-primary/90 transition-colors",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {isSubmitting ? (
                <div className="h-5 w-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleDemoMode}
              disabled={isSubmitting}
              className={cn(
                "w-full flex items-center justify-center space-x-2",
                "px-4 py-2 rounded-lg font-medium",
                "bg-secondary text-secondary-foreground",
                "hover:bg-secondary/80 transition-colors",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {isSubmitting ? (
                <div className="h-5 w-5 border-2 border-secondary-foreground/30 border-t-secondary-foreground rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Try Demo Mode</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Demo credentials: demo@certifystudio.ai / demo123
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Don't have an account?{' '}
              <a href="#" className="text-primary hover:underline">
                Request Access
              </a>
            </p>
          </div>
        </motion.div>
      </div>

      {/* Right side - Feature showcase */}
      <div className="hidden lg:flex flex-1 items-center justify-center p-8 bg-gradient-to-br from-blue-600 to-purple-700 text-white relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-black/20" />
          <div className="absolute top-0 left-0 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        </div>

        <div className="relative z-10 max-w-lg">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold mb-6">
              Welcome to the Future of Educational Content
            </h2>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="h-8 w-8 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
                  <Brain className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Autonomous AI Agents</h3>
                  <p className="text-white/80 text-sm">
                    Multiple specialized agents collaborate to create optimal learning experiences
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="h-8 w-8 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Cognitive Load Optimization</h3>
                  <p className="text-white/80 text-sm">
                    Content automatically adapts to human cognitive capabilities
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="h-8 w-8 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
                  <ArrowRight className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Multi-Format Generation</h3>
                  <p className="text-white/80 text-sm">
                    Create videos, interactive content, VR experiences, and more
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}