# Motion Canvas Implementation Guide for Certify Studio

## Quick Start Commands

```bash
# Create new Motion Canvas project for Certify Studio
npm create @motion-canvas/video@latest certify-studio-animations

# Navigate to project
cd certify-studio-animations

# Install dependencies
npm install

# Start development server
npm run serve

# Build/render animation
npm run build
```

## Project Structure for Certify Studio

```
certify-studio-animations/
├── src/
│   ├── project.ts                    # Main project config
│   ├── components/
│   │   ├── aws/
│   │   │   ├── AWSServiceCard.tsx   # Reusable service component
│   │   │   ├── AWSIcon.tsx          # Icon wrapper component
│   │   │   └── AWSColors.ts         # AWS brand colors
│   │   ├── layouts/
│   │   │   ├── FlowDiagram.tsx      # Flow diagram component
│   │   │   ├── ComparisonView.tsx   # Side-by-side comparison
│   │   │   └── HierarchyTree.tsx    # Hierarchical view
│   │   └── animations/
│   │       ├── Reveal.ts            # Reveal animation patterns
│   │       ├── Flow.ts              # Flow animation patterns
│   │       └── Transitions.ts       # Transition patterns
│   ├── scenes/
│   │   ├── aws-ai-practitioner/
│   │   │   ├── domain1/
│   │   │   │   ├── overview.tsx     # Domain 1 main flow
│   │   │   │   ├── topic1-1.tsx     # AI concepts
│   │   │   │   ├── topic1-2.tsx     # ML types
│   │   │   │   └── topic1-3.tsx     # AWS services
│   │   │   └── components.tsx       # Shared components
│   └── assets/
│       ├── icons/
│       │   └── aws/                  # AWS service icons
│       └── fonts/                    # Custom fonts
├── audio/                            # Narration files
├── output/                           # Rendered videos
└── package.json
```

## First Component to Build: AWSServiceCard

```typescript
// src/components/aws/AWSServiceCard.tsx
import {Rect, Text, Icon, Layout} from '@motion-canvas/2d/lib/components';
import {Reference, createRef} from '@motion-canvas/core/lib/flow';
import {easeOutCubic} from '@motion-canvas/core/lib/tweening';

export interface AWSServiceCardProps {
  serviceName: string;
  serviceIcon: string;
  description?: string;
  color?: string;
  position?: [number, number];
}

export class AWSServiceCard extends Layout {
  private container = createRef<Rect>();
  private icon = createRef<Icon>();
  private title = createRef<Text>();
  private desc = createRef<Text>();
  
  public constructor(props: AWSServiceCardProps) {
    super({
      position: props.position || [0, 0],
    });
    
    const awsOrange = '#FF9900';
    const awsNavy = '#232F3E';
    
    this.add(
      <Rect
        ref={this.container}
        size={[280, 200]}
        fill={props.color || awsNavy}
        radius={12}
        shadowColor={'rgba(0,0,0,0.2)'}
        shadowBlur={20}
        shadowOffset={[0, 10]}
      >
        <Layout direction={'column'} gap={20} padding={30}>
          <Icon
            ref={this.icon}
            icon={props.serviceIcon}
            size={64}
            color={awsOrange}
          />
          <Text
            ref={this.title}
            text={props.serviceName}
            fontSize={24}
            fontWeight={700}
            fill={'white'}
          />
          {props.description && (
            <Text
              ref={this.desc}
              text={props.description}
              fontSize={16}
              fill={'rgba(255,255,255,0.8)'}
              textWrap={true}
              width={220}
            />
          )}
        </Layout>
      </Rect>
    );
  }
  
  public *animateIn(duration: number = 0.8) {
    // Start state
    this.container().scale(0.8);
    this.container().opacity(0);
    
    // Animate
    yield* all(
      this.container().scale(1, duration, easeOutCubic),
      this.container().opacity(1, duration * 0.6),
    );
  }
  
  public *highlight() {
    yield* this.container().scale(1.05, 0.3);
    yield* this.container().scale(1, 0.3);
  }
}
```

## First Scene: AI vs ML Comparison

```typescript
// src/scenes/aws-ai-practitioner/domain1/topic1-1.tsx
import {makeScene2D} from '@motion-canvas/2d/lib/scenes';
import {Text, Rect, Line} from '@motion-canvas/2d/lib/components';
import {all, sequence, waitFor} from '@motion-canvas/core/lib/flow';
import {createRef} from '@motion-canvas/core/lib/utils';
import {AWSServiceCard} from '../../../components/aws/AWSServiceCard';

export default makeScene2D(function* (view) {
  // Scene setup
  view.fill('#1a1a1a'); // Dark background
  
  // Title
  const title = createRef<Text>();
  view.add(
    <Text
      ref={title}
      text={'AI vs Machine Learning'}
      fontSize={56}
      fontWeight={700}
      fill={'white'}
      y={-350}
      opacity={0}
    />
  );
  
  // AI Box
  const aiBox = createRef<Rect>();
  const aiText = createRef<Text>();
  
  view.add(
    <Rect
      ref={aiBox}
      size={[400, 300]}
      fill={'#FF9900'}
      radius={16}
      x={-300}
      y={0}
      opacity={0}
    >
      <Text
        ref={aiText}
        text={'Artificial Intelligence'}
        fontSize={32}
        fontWeight={600}
        fill={'white'}
        y={-100}
      />
      <Text
        text={'Broad concept of machines\nbeing able to carry out\ntasks in a "smart" way'}
        fontSize={20}
        fill={'white'}
        y={20}
        textAlign={'center'}
        lineHeight={1.5}
      />
    </Rect>
  );
  
  // ML Box (subset of AI)
  const mlBox = createRef<Rect>();
  
  view.add(
    <Rect
      ref={mlBox}
      size={[350, 250]}
      fill={'#146EB4'}
      radius={16}
      x={300}
      y={0}
      opacity={0}
    >
      <Text
        text={'Machine Learning'}
        fontSize={32}
        fontWeight={600}
        fill={'white'}
        y={-80}
      />
      <Text
        text={'Subset of AI that uses\nalgorithms to learn\nfrom data'}
        fontSize={20}
        fill={'white'}
        y={20}
        textAlign={'center'}
        lineHeight={1.5}
      />
    </Rect>
  );
  
  // Connection arrow
  const arrow = createRef<Line>();
  view.add(
    <Line
      ref={arrow}
      points={[[-100, 0], [100, 0]]}
      stroke={'white'}
      lineWidth={4}
      endArrow
      opacity={0}
    />
  );
  
  // Animation sequence
  yield* title().opacity(1, 1);
  yield* waitFor(0.5);
  
  yield* sequence(0.3,
    aiBox().opacity(1, 0.8),
    mlBox().opacity(1, 0.8),
    arrow().opacity(1, 0.6),
  );
  
  yield* waitFor(1);
  
  // Highlight relationship
  yield* all(
    mlBox().scale(0.9, 0.5),
    mlBox().position.x(150, 0.5),
    arrow().points([[-100, 0], [-50, 0]], 0.5),
  );
  
  yield* waitFor(2);
});
```

## AWS Brand Colors Reference

```typescript
// src/components/aws/AWSColors.ts
export const AWSColors = {
  // Primary
  orange: '#FF9900',
  navy: '#232F3E',
  
  // Secondary
  lightBlue: '#146EB4',
  darkBlue: '#0073BB',
  
  // Service specific
  sagemaker: '#FF9900',
  comprehend: '#146EB4',
  rekognition: '#FF9900',
  textract: '#146EB4',
  
  // Backgrounds
  darkBg: '#1a1a1a',
  lightBg: '#f5f5f5',
  
  // Text
  textPrimary: '#ffffff',
  textSecondary: 'rgba(255,255,255,0.8)',
} as const;
```

## Next Steps in New Session

1. **Set up Motion Canvas project** with this structure
2. **Create AWSServiceCard component** with animations
3. **Build first scene** (AI vs ML comparison)
4. **Add AWS service icons** (download from AWS Architecture Icons)
5. **Test render quality** and compare with ByteByteGo
6. **Iterate on animations** to achieve desired quality

## Remember

- Motion Canvas uses generators (`function*`) for animations
- `yield*` is used to wait for animations to complete
- Components are React-like but for animations
- Real-time preview in browser during development
- Export to MP4/WebM for final output

This gives you everything needed to continue in a new session!