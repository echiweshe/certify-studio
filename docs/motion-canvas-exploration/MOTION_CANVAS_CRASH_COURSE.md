# Motion Canvas Crash Course & AWS AI Practitioner Implementation

## What is Motion Canvas?

Motion Canvas is a TypeScript/JavaScript library for creating programmatic animations, designed as a modern alternative to Manim. It's specifically built for web-based animations with better tooling and developer experience.

### Key Advantages over Manim:
- **TypeScript-based**: Better IDE support, type safety
- **Real-time preview**: See changes instantly in browser
- **Component-based**: Reusable animation components
- **Better performance**: Optimized for web
- **Modern tooling**: Vite, React-like syntax
- **Easier styling**: CSS-like properties

## Installation & Setup

```bash
# Create new Motion Canvas project
npm create @motion-canvas/video@latest

# Project structure
my-animation/
├── src/
│   ├── project.ts       # Project configuration
│   ├── scenes/          # Animation scenes
│   └── components/      # Reusable components
├── audio/               # Audio files
└── output/             # Rendered videos
```

## Basic Motion Canvas Example

```typescript
// src/scenes/example.tsx
import {makeScene2D} from '@motion-canvas/2d/lib/scenes';
import {Circle, Rect, Text} from '@motion-canvas/2d/lib/components';
import {all, createRef} from '@motion-canvas/core/lib/flow';

export default makeScene2D(function* (view) {
  // Create references to animate
  const circle = createRef<Circle>();
  const rect = createRef<Rect>();
  
  // Add components to scene
  view.add(
    <>
      <Circle
        ref={circle}
        size={120}
        fill={'#e13238'}
        position={[-200, 0]}
      />
      <Rect
        ref={rect}
        size={[120, 120]}
        fill={'#ffc107'}
        position={[200, 0]}
      />
    </>
  );
  
  // Animate!
  yield* all(
    circle().scale(2, 1),
    rect().rotation(360, 2),
  );
});
```

## AWS AI Practitioner Domain 1 Structure

```typescript
// AWS AI Practitioner - Domain 1: Fundamentals of AI and ML (20%)
interface Domain1 {
  name: "Fundamentals of AI and ML";
  weight: "20%";
  topics: {
    "1.1": {
      name: "Explain basic AI concepts and terminologies";
      concepts: [
        "Define AI, ML, deep learning",
        "Neural networks basics",
        "Computer vision & NLP",
        "Training vs inference"
      ]
    },
    "1.2": {
      name: "Describe ML types";
      concepts: [
        "Supervised learning",
        "Unsupervised learning",
        "Reinforcement learning",
        "Real-world applications"
      ]
    }
  }
}
```

## ByteByteGo-Style Component Example

```typescript
// src/components/AWSService.tsx
import {Rect, Text, Icon} from '@motion-canvas/2d/lib/components';
import {createRef} from '@motion-canvas/core/lib/flow';

export interface AWSServiceProps {
  name: string;
  icon: string;
  color: string;
  position: [number, number];
}

export function AWSService({name, icon, color, position}: AWSServiceProps) {
  const container = createRef<Rect>();
  
  return (
    <Rect
      ref={container}
      size={[200, 150]}
      fill={color}
      radius={8}
      position={position}
      opacity={0}
    >
      <Icon
        icon={icon}
        size={64}
        y={-20}
      />
      <Text
        text={name}
        fontSize={24}
        fill={'white'}
        y={40}
      />
    </Rect>
  );
}

// Animation method
export function* animateServiceEntry(service: Rect, delay: number = 0) {
  yield* waitFor(delay);
  yield* service.opacity(1, 0.5);
  yield* service.scale([0.8, 0.8], [1, 1], 0.3);
}
```

## Sample AWS AI Practitioner Animation

```typescript
// src/scenes/ai-fundamentals.tsx
import {makeScene2D} from '@motion-canvas/2d/lib/scenes';
import {AWSService, animateServiceEntry} from '../components/AWSService';

export default makeScene2D(function* (view) {
  // Title
  const title = createRef<Text>();
  view.add(
    <Text
      ref={title}
      text="AWS AI Services Overview"
      fontSize={48}
      fill={'white'}
      y={-300}
      opacity={0}
    />
  );
  
  // AWS Services
  const services = [
    {name: 'SageMaker', icon: 'sagemaker.svg', color: '#FF9900', position: [-400, 0]},
    {name: 'Comprehend', icon: 'comprehend.svg', color: '#232F3E', position: [0, 0]},
    {name: 'Rekognition', icon: 'rekognition.svg', color: '#FF9900', position: [400, 0]},
  ];
  
  const serviceRefs = services.map(service => {
    const ref = createRef<Rect>();
    view.add(<AWSService {...service} ref={ref} />);
    return ref;
  });
  
  // Animate sequence
  yield* title().opacity(1, 1);
  yield* waitFor(0.5);
  
  // Animate services in sequence
  for (let i = 0; i < serviceRefs.length; i++) {
    yield* animateServiceEntry(serviceRefs[i](), i * 0.3);
  }
  
  // Add connecting lines
  yield* drawConnectionLines(serviceRefs);
});
```

## Motion Canvas vs Manim Comparison

| Feature | Motion Canvas | Manim |
|---------|--------------|--------|
| Language | TypeScript/JavaScript | Python |
| Preview | Real-time in browser | Render to see |
| Components | React-like components | Class-based |
| Styling | CSS-like | Method calls |
| Performance | Optimized for web | Better for complex math |
| Learning Curve | Easier for web devs | Easier for Python devs |
| Output | MP4, WebM, GIF | MP4 primarily |

## Next Steps for Implementation

1. **Set up Motion Canvas project** for Certify Studio
2. **Create component library** for AWS services
3. **Build animation patterns** (reveal, flow, transition)
4. **Implement Domain 1** as proof of concept
5. **Compare output quality** with ByteByteGo

## Key Files to Create

```
certify-studio/
├── animation-engine/
│   ├── motion-canvas/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── AWSService.tsx
│   │   │   │   ├── DiagramFlow.tsx
│   │   │   │   └── AnimatedIcon.tsx
│   │   │   ├── scenes/
│   │   │   │   └── aws-ai-fundamentals.tsx
│   │   │   └── styles/
│   │   │       └── bytebytego.ts
│   │   └── package.json
│   └── assets/
│       └── icons/
│           └── aws/
└── docs/
    └── motion-canvas-exploration/
```